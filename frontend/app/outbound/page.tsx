'use client';

import Link from 'next/link';
import { useRef, useState } from 'react';
import { Room, RoomEvent, type TranscriptionSegment } from 'livekit-client';
import { Button } from '@/components/ui/button';

type Status = 'idle' | 'dispatching' | 'live' | 'done' | 'error';

type LeadData = {
  budget_eur: string;
  timeline: string;
  use_case: string;
  interest_level: string;
  is_decision_maker: boolean;
  notes: string;
};

type TranscriptLine = { id: string; speaker: string; text: string };

export default function OutboundPage() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('+49');
  const [context, setContext] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [lead, setLead] = useState<LeadData | null>(null);
  const roomRef = useRef<Room | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (status === 'dispatching' || status === 'live') return;
    setStatus('dispatching');
    setErrorMsg('');
    setTranscript([]);
    setLead(null);

    try {
      // 1. Dispatch: erstellt Room + triggert Outbound-Call
      const dispatchRes = await fetch('/api/dispatch-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone, context }),
      });
      const dispatchData = await dispatchRes.json();
      if (!dispatchRes.ok) throw new Error(dispatchData.error || 'Dispatch fehlgeschlagen.');

      // 2. Observer-Token für denselben Room holen
      const tokenRes = await fetch('/api/observer-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roomName: dispatchData.roomName }),
      });
      const tokenData = await tokenRes.json();
      if (!tokenRes.ok) throw new Error(tokenData.error || 'Token-Request fehlgeschlagen.');

      // 3. Als stiller Beobachter im Room subscriben
      const room = new Room();
      roomRef.current = room;

      room.on(RoomEvent.TranscriptionReceived, (segments: TranscriptionSegment[], participant) => {
        for (const seg of segments) {
          if (!seg.final) continue;
          const speaker = participant?.identity?.startsWith('caller') ? 'Anrufer' : 'Agent';
          setTranscript((prev) => {
            if (prev.some((l) => l.id === seg.id)) return prev;
            return [...prev, { id: seg.id, speaker, text: seg.text }];
          });
        }
      });

      room.on(RoomEvent.DataReceived, (payload) => {
        try {
          const msg = JSON.parse(new TextDecoder().decode(payload));
          if (msg.type === 'lead_qualified') {
            setLead(msg.data as LeadData);
          }
        } catch {
          /* non-JSON data-message ignorieren */
        }
      });

      room.on(RoomEvent.Disconnected, () => {
        setStatus((s) => (s === 'error' ? s : 'done'));
      });

      await room.connect(tokenData.url, tokenData.token);
      setStatus('live');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Fehler beim Anruf-Start');
      setStatus('error');
    }
  }

  async function handleReset() {
    await roomRef.current?.disconnect();
    roomRef.current = null;
    setStatus('idle');
    setTranscript([]);
    setLead(null);
    setErrorMsg('');
  }

  return (
    <main className="bg-background min-h-svh px-6 py-12">
      <div className="mx-auto max-w-3xl">
        <nav className="mb-8">
          <Link href="/" className="text-muted-foreground text-sm hover:underline">
            ← Zurück zur Agent-Auswahl
          </Link>
        </nav>

        <h1 className="text-3xl font-bold tracking-tight">Outbound Lead Qualifier</h1>
        <p className="text-muted-foreground mt-2 mb-8">
          Trag Name und Handy-Nummer ein. Der Voice-Agent ruft dich innerhalb weniger Sekunden
          an und führt ein kurzes Qualifikations-Gespräch.
        </p>

        {status === 'idle' || status === 'error' ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Dein Name</label>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
                placeholder="Max Mustermann"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Telefonnummer (E.164)</label>
              <input
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                pattern="^\+\d{8,15}$"
                className="border-input bg-background w-full rounded-md border px-3 py-2 font-mono text-sm"
                placeholder="+491701234567"
              />
              <p className="text-muted-foreground mt-1 text-xs">
                Format: +[Ländervorwahl][Nummer] ohne Leerzeichen, z. B. +491701234567
              </p>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Dein Anliegen (optional)
              </label>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                rows={3}
                className="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
                placeholder="z. B. Suche einen DSGVO-konformen Voice-Bot für meine Praxis"
              />
            </div>

            {errorMsg && (
              <div className="border-destructive/40 bg-destructive/10 text-destructive rounded-md border p-3 text-sm">
                {errorMsg}
              </div>
            )}

            <Button type="submit" className="w-full">
              Ruf mich an
            </Button>
          </form>
        ) : (
          <div className="space-y-6">
            <StatusPill status={status} />

            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
                Live-Transkript
              </h2>
              {transcript.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  Noch keine Sprachsegmente erkannt…
                </p>
              ) : (
                <ul className="space-y-2">
                  {transcript.map((line) => (
                    <li
                      key={line.id}
                      className="border-l-primary bg-muted/30 rounded-r-md border-l-4 px-3 py-2 text-sm"
                    >
                      <span className="text-muted-foreground font-mono text-xs">
                        {line.speaker}:
                      </span>{' '}
                      {line.text}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {lead && (
              <section>
                <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
                  Qualifikations-Ergebnis
                </h2>
                <dl className="bg-muted/30 grid grid-cols-[minmax(140px,auto)_1fr] gap-x-4 gap-y-2 rounded-md p-4 text-sm">
                  <dt className="text-muted-foreground">Budget</dt>
                  <dd>{lead.budget_eur}</dd>
                  <dt className="text-muted-foreground">Zeitplan</dt>
                  <dd>{lead.timeline}</dd>
                  <dt className="text-muted-foreground">Use Case</dt>
                  <dd>{lead.use_case}</dd>
                  <dt className="text-muted-foreground">Interesse</dt>
                  <dd className="font-medium">{lead.interest_level}</dd>
                  <dt className="text-muted-foreground">Entscheider?</dt>
                  <dd>{lead.is_decision_maker ? 'Ja' : 'Nein'}</dd>
                  {lead.notes && (
                    <>
                      <dt className="text-muted-foreground">Notizen</dt>
                      <dd>{lead.notes}</dd>
                    </>
                  )}
                </dl>
              </section>
            )}

            <Button variant="outline" onClick={handleReset}>
              Neuer Anruf
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}

function StatusPill({ status }: { status: Status }) {
  const labels: Record<Exclude<Status, 'idle'>, { text: string; tone: string }> = {
    dispatching: { text: 'Anruf wird gestartet…', tone: 'bg-yellow-500/10 text-yellow-700' },
    live: { text: 'Gespräch läuft', tone: 'bg-green-500/10 text-green-700' },
    done: { text: 'Gespräch beendet', tone: 'bg-gray-500/10 text-gray-700' },
    error: { text: 'Fehler', tone: 'bg-red-500/10 text-red-700' },
  };
  const entry = status === 'idle' ? null : labels[status];
  if (!entry) return null;
  return (
    <div
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${entry.tone}`}
    >
      {entry.text}
    </div>
  );
}
