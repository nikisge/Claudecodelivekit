# LiveKit Voice Agents — DSGVO-konform, selbst gehostet

Begleit-Repo zum YouTube-Tutorial. Drei Voice Agents, die zeigen, wie man mit [LiveKit](https://livekit.io) und [Claude Code](https://claude.com/claude-code) schnell produktionsreife Voice-AI baut — **DSGVO-konform** und **auf dem eigenen VPS** statt bei US-SaaS-Anbietern.

## Die drei Agents

| # | Agent | Was er demonstriert |
|---|---|---|
| **01** | `simple-latency` | Basis-Pipeline STT → LLM → TTS, auf niedrige Latenz optimiert. Gemini 2.5 Flash Lite + Deepgram EU + Cartesia Sonic (deutsche Stimme). |
| **02** | `appointment-booking` | Function Calling gegen echte Google Calendar API. Termine buchen, verschieben, absagen — per Sprache. Azure OpenAI GPT-4.1 mini + Deepgram EU + ElevenLabs „Johanna". |
| **03** | `outbound-lead-qualifier` | Outbound-Call via Twilio SIP. Zuschauer füllt Formular aus → wird angerufen → Agent qualifiziert Lead → strukturiertes JSON-Ergebnis. |

## Quickstart (lokal auf Mac)

```bash
git clone <dein-fork>
cd livekit-voice-agents-de
./scripts/generate-keys.sh                # erstellt .env + LiveKit-Keys
# .env füllen: siehe docs/credentials-setup.md (Deepgram, Cartesia, GCP, Azure, ElevenLabs)

./start.sh setup                          # einmalig: Images bauen + Container anlegen (~5 Min)
./start.sh                                # Infra starten (LiveKit + Frontend)
```

`http://localhost:3000` öffnen. Jede Agent-Kachel hat einen eigenen Start/Stop-Button — Agent-Container werden on-demand gestartet, damit der erste `up` nicht ewig dauert.

Hot-Reload beim Agent-Entwickeln (optional, statt Docker):
```bash
cd agents/01-simple-latency
uv sync && uv run python agent.py dev
```

Für VPS-Deployment → siehe `docs/vps-deployment.md`.
Credentials-Setup → siehe `docs/credentials-setup.md`.

## Architektur (VPS-Produktion)

```
Internet ──┬─▶ Caddy (Auto-TLS) ──┬─▶ Frontend (Next.js)
           │                      └─▶ LiveKit-Server (WebSocket)
           └─▶ Twilio SIP Trunk ──────▶ LiveKit-SIP ──▶ LiveKit-Server
                                                           │
                                                           ├─▶ Agent 1 (Python)
                                                           ├─▶ Agent 2 (Python)
                                                           └─▶ Agent 3 (Python)
```

Alle Agents verbinden sich als LiveKit-Worker zum Server und warten auf Dispatch.

## DSGVO-Konformität

Jeder verwendete Service läuft in einer EU-Region oder bietet Zero-Retention-Mode. Details und die nötigen DPAs: `docs/dsgvo-compliance.md`.

**Bewusst nicht in diesem Repo:**
- OpenAI direkt (nur Azure EU)
- US-gehostete STT/TTS ohne EU-Residency
- Avatar-Services (Tavus/Beyond Presence — alle US-SaaS)

## Projekt-Struktur

```
livekit-voice-agents-de/
├── docker-compose.yml          # VPS-Prod
├── docker-compose.local.yml    # Mac-lokal
├── Caddyfile                   # TLS-Reverse-Proxy
├── livekit.yaml                # LiveKit-Config (VPS)
├── livekit.local.yaml          # LiveKit-Config (Mac)
├── .env.example                # Env-Template mit DSGVO-Kommentaren
│
├── agents/                     # Drei Voice-Agents in Python
├── frontend/                   # Next.js-UI (Browser-Test + Outbound-Formular)
├── scripts/                    # Setup-Helfer (Keys, SIP)
└── docs/                       # Deutschsprachige Setup-Guides
```

## Tutorial-Video

→ (Link wird nach Veröffentlichung ergänzt)

## Lizenz

MIT
