# Voice-Agent-Konzepte (für Video-Zuschauer)

Diese Seite erklärt die wichtigsten Konzepte, die im Video-Tutorial vorkommen, in kompakter Form — gedacht als Nachschlagewerk, nicht als Pflichtlektüre.

## Die STT→LLM→TTS-Pipeline

```
Mikrofon  ──▶  STT (Speech-to-Text)  ──▶  LLM  ──▶  TTS (Text-to-Speech)  ──▶  Lautsprecher
   │                     │                   │              │
   │                     │                   │              │
   └── VAD (Voice Activity Detection) + Turn Detection ─────┘
```

Jeder Pfeil ist eine eigene Latenz-Quelle. Die Summe ergibt die **End-to-End-Antwortzeit**, die das Gespräch entweder natürlich oder träge wirken lässt.

## VAD vs. Turn Detection

**VAD** (Voice Activity Detection) erkennt: „Kommt gerade Sprache aus dem Mikrofon?" — binär, pro Audio-Frame.

**Turn Detection** erkennt: „Hat der Nutzer seinen Turn fertig gesprochen, oder macht er nur eine Atempause?" — semantisch, nutzt dafür ein kleines Sprachmodell.

Pure Silence-Detection (nur VAD, „wenn 500ms Stille dann Turn-Ende") schaltet oft zu früh um, wenn der User nachdenkt. LiveKit's Multilingual Turn Detection Model prüft den bisherigen Transkript-Text mit und wartet länger, wenn der Satz unvollständig wirkt.

## Function Calling / Tool Use

Der LLM kann „Tools" aufrufen, die in Python definiert sind (mit `@function_tool`-Dekorator). Beispiel aus Agent 2:

```python
@function_tool()
async def book_appointment(self, context, start_iso: str, name: str, duration_min: int = 30):
    """Bucht einen Termin."""
    result = self._calendar.book(start_iso, duration_min, name)
    return f"Termin gebucht: {name}, {result['start']}."
```

Flow:
1. Nutzer sagt: „Buche bitte Freitag 14 Uhr, ich bin Max."
2. LLM entscheidet: Tool `book_appointment` aufrufen mit Args `start_iso=2026-04-24T14:00:00+02:00`, `name=Max`
3. Python-Code wird ausgeführt, Rückgabe geht zurück an LLM
4. LLM generiert die Sprach-Antwort an den Nutzer: „Alles klar Max, ich habe den Termin für Freitag 14 Uhr eingetragen."

## Realtime-Models (nicht in diesem Tutorial genutzt, aber gut zu kennen)

OpenAI Realtime API und Gemini Live API bieten ein **anderes** Modell: statt STT→LLM→TTS-Chain sprechen sie direkt Audio ↔ Audio. Vorteile:
- Noch niedrigere Latenz
- Emotionale Prosodie (Modell hört Tonfall)

Nachteile:
- Weniger Kontrolle (keine Zwischenschritte zum Debuggen)
- Meist teurer
- DSGVO-Situation je nach Anbieter komplizierter

Für Lerzwecke ist die klassische Pipeline klarer, deshalb nutzen wir die in diesem Tutorial.

## Worker-Pattern (Agent 3)

Agent 1 und 2 kannst du lokal im „Dev-Mode" starten (`python agent.py dev`) und jedes Mal ein frischer Agent-Prozess pro Gespräch. Für Produktion und Outbound-Calls brauchst du den **Worker-Mode** (`python agent.py start`):

```
Worker läuft permanent
   │
   ├── wartet auf Dispatches vom LiveKit-Server
   │
   └── bei Dispatch: spawnt Agent-Instanz in einem Room
```

Das Frontend (`POST /api/dispatch-call`) triggert so einen Dispatch inkl. Room-Anlage und SIP-Call-Start.

## Data Channel

LiveKit erlaubt Peer-to-Peer-Daten-Messages innerhalb eines Rooms, zusätzlich zu Audio. Agent 3 nutzt das, um am Gesprächsende das qualifizierte Lead-JSON ans Frontend zu pushen:

```python
await context.room.local_participant.publish_data(
    payload=json.dumps({"type": "lead_qualified", "data": lead}).encode(),
    reliable=True,
)
```

Im Browser (Observer-Token, read-only):

```typescript
room.on(RoomEvent.DataReceived, (payload) => {
  const msg = JSON.parse(new TextDecoder().decode(payload));
  if (msg.type === 'lead_qualified') setLead(msg.data);
});
```

## Warum 3 verschiedene LLMs?

| Agent | Ziel | Gewählt | Warum |
|---|---|---|---|
| 01 | minimal latency | Gemini 2.5 Flash Native Audio | Speech-to-Speech ohne separaten STT/TTS-Hop |
| 02 | Tool Calling, strukturierte Args | Azure GPT-4.1 mini | bessere Tool-Intent-Erkennung als Flash Lite |
| 03 | Gespräch + Tool Calling | Azure GPT-4.1 mini | wie Agent 02 — Qualifikation braucht Intelligenz, Latenz ist im Telefonat weniger kritisch |

Im Repo tauschst du den Provider an *einer* Stelle (im `AgentSession(llm=...)`-Call), der Rest bleibt gleich.
