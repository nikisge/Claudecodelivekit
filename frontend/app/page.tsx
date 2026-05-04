'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

type AgentKey = 'simple-latency' | 'appointment-booking' | 'outbound-telephony';
type AgentState = 'running' | 'stopped' | 'starting' | 'missing';

type AgentCardData = {
  key: AgentKey;
  href: string;
  badge: string;
  title: string;
  description: string;
  stack: string;
};

const AGENTS: AgentCardData[] = [
  {
    key: 'simple-latency',
    href: '/agent/simple-latency',
    badge: '01 · Latency',
    title: 'Simple Latency',
    description:
      'Minimale STT→LLM→TTS-Pipeline. Zeigt das Grundprinzip eines Voice-Agents in ~80 Zeilen Code.',
    stack: 'Gemini 2.5 Flash Lite · Deepgram EU · Azure Speech',
  },
  {
    key: 'appointment-booking',
    href: '/agent/appointment-booking',
    badge: '02 · Tool Calling',
    title: 'Termin-Assistent',
    description:
      'Bucht, verschiebt und sagt Termine in einem echten Google Kalender ab. Zeigt Multi-Turn-Tool-Calling.',
    stack: 'Azure OpenAI GPT-4.1 mini · Azure Speech',
  },
  {
    key: 'outbound-telephony',
    href: '/outbound',
    badge: '03 · Telephony',
    title: 'Outbound-Anruf',
    description:
      'Formular ausfüllen, der Agent ruft dich per Twilio SIP an und qualifiziert dein Anliegen.',
    stack: 'Azure OpenAI · Twilio SIP (nur auf VPS)',
  },
];

export default function LandingPage() {
  const [statuses, setStatuses] = useState<Record<AgentKey, AgentState>>({
    'simple-latency': 'stopped',
    'appointment-booking': 'stopped',
    'outbound-telephony': 'stopped',
  });
  const [busy, setBusy] = useState<Record<AgentKey, boolean>>({
    'simple-latency': false,
    'appointment-booking': false,
    'outbound-telephony': false,
  });
  const [error, setError] = useState<string>('');

  async function refresh() {
    try {
      const res = await fetch('/api/agent/status', { cache: 'no-store' });
      if (!res.ok) return;
      const data = (await res.json()) as { agents: Record<AgentKey, AgentState> };
      setStatuses(data.agents);
    } catch {
      /* silent */
    }
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, []);

  async function handleStart(key: AgentKey) {
    setBusy((b) => ({ ...b, [key]: true }));
    setError('');
    try {
      const res = await fetch('/api/agent/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: key }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.error || 'Start fehlgeschlagen');
      }
      setStatuses((s) => ({ ...s, [key]: 'starting' }));
      setTimeout(refresh, 1500);
    } finally {
      setBusy((b) => ({ ...b, [key]: false }));
    }
  }

  async function handleStop(key: AgentKey) {
    setBusy((b) => ({ ...b, [key]: true }));
    try {
      await fetch('/api/agent/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: key }),
      });
      setTimeout(refresh, 1000);
    } finally {
      setBusy((b) => ({ ...b, [key]: false }));
    }
  }

  return (
    <main className="bg-background min-h-svh px-6 py-16">
      <div className="mx-auto max-w-5xl">
        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            Voice Agents — DSGVO-konform
          </h1>
          <p className="text-muted-foreground mx-auto mt-4 max-w-2xl">
            Drei Voice-Agents zum Testen. Starte einen Agent, öffne die Demo und sprich
            drauflos. Nach dem Gespräch kannst du ihn wieder stoppen.
          </p>
        </header>

        {error && (
          <div className="border-destructive/40 bg-destructive/10 text-destructive mb-6 rounded-md border p-3 text-sm">
            {error}
          </div>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          {AGENTS.map((agent) => (
            <AgentCard
              key={agent.key}
              agent={agent}
              state={statuses[agent.key]}
              busy={busy[agent.key]}
              onStart={() => handleStart(agent.key)}
              onStop={() => handleStop(agent.key)}
            />
          ))}
        </section>

        <footer className="text-muted-foreground mt-12 text-center text-xs">
          Erster Start eines Agents dauert 5–15 Sek (Model-Load). Jeder weitere Start
          ist sofort.
        </footer>
      </div>
    </main>
  );
}

function AgentCard({
  agent,
  state,
  busy,
  onStart,
  onStop,
}: {
  agent: AgentCardData;
  state: AgentState;
  busy: boolean;
  onStart: () => void;
  onStop: () => void;
}) {
  const isRunning = state === 'running';
  const isStarting = state === 'starting' || busy;
  const isMissing = state === 'missing';

  return (
    <div className="border-border bg-background flex flex-col rounded-2xl border p-6 transition-colors">
      <div className="flex items-start justify-between">
        <span className="text-muted-foreground font-mono text-xs tracking-wider uppercase">
          {agent.badge}
        </span>
        <StateBadge state={state} />
      </div>

      <h2 className="mt-2 text-xl font-bold">{agent.title}</h2>
      <p className="text-muted-foreground mt-2 flex-1 text-sm leading-relaxed">
        {agent.description}
      </p>
      <p className="text-muted-foreground/80 mt-4 font-mono text-xs">{agent.stack}</p>

      <div className="mt-4 flex gap-2">
        {!isRunning && (
          <Button
            size="sm"
            className="flex-1"
            disabled={isStarting || isMissing}
            onClick={onStart}
          >
            {isStarting ? 'Startet…' : isMissing ? 'Image fehlt' : 'Start'}
          </Button>
        )}
        {isRunning && (
          <>
            <Button size="sm" asChild className="flex-1">
              <Link href={agent.href}>Öffnen →</Link>
            </Button>
            <Button size="sm" variant="outline" onClick={onStop} disabled={busy}>
              Stop
            </Button>
          </>
        )}
      </div>

      {isMissing && (
        <p className="text-muted-foreground mt-2 font-mono text-[10px] leading-relaxed">
          docker compose --profile all-agents build
        </p>
      )}
    </div>
  );
}

function StateBadge({ state }: { state: AgentState }) {
  const config: Record<AgentState, { label: string; cls: string }> = {
    running: { label: 'aktiv', cls: 'bg-green-500/15 text-green-700' },
    starting: { label: 'startet', cls: 'bg-yellow-500/15 text-yellow-700' },
    stopped: { label: 'gestoppt', cls: 'bg-gray-500/15 text-gray-600' },
    missing: { label: 'nicht gebaut', cls: 'bg-gray-500/15 text-gray-500' },
  };
  const c = config[state];
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${c.cls}`}>
      {c.label}
    </span>
  );
}
