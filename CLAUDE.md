# CLAUDE.md

Guidance für Claude Code, wenn er in diesem Repo arbeitet.

## Projekt-Kontext

Begleit-Repo zu einem YouTube-Tutorial (deutsch) über DSGVO-konforme Voice Agents mit LiveKit. **Drei Agents** für unterschiedliche Lern-Etappen:

| # | Name | Demonstriert |
|---|---|---|
| 01 | `simple-latency` | Minimale STT→LLM→TTS-Pipeline, optimiert auf Latenz (Gemini 2.5 Flash Lite + Deepgram + Cartesia) |
| 02 | `appointment-booking` | Multi-Turn Tool-Calling gegen Google Calendar (Azure OpenAI + ElevenLabs "Johanna") |
| 03 | `outbound-telephony` | Twilio SIP Outbound-Calls (**nur auf VPS** sinnvoll, nicht lokal) |

Zielgruppe: Zuschauer, die das Repo klonen und mitbauen. Jede Änderung sollte damit verträglich sein — keine Abhängigkeiten außerhalb dessen, was in `docs/credentials-setup.md` aufgeführt ist.

## DSGVO-Prinzip

**Alle Services in EU-Region oder Zero-Retention.** Bewusst **nicht** in diesem Repo: OpenAI direkt (nur Azure EU Data Zone), US-STT/TTS ohne EU-Residency, Avatar-Services (Tavus/Beyond Presence — alle US-SaaS).

Bei Provider-Wahl gilt: **Latenz > Intelligenz**. Für Voice-Agents ist das konsistent latenzärmste DSGVO-konforme Modell die richtige Wahl, auch wenn ein US-Modell "schlauer" wäre.

## Architektur

```
Browser → Frontend (Next.js)  → /api/token       (LiveKit-JWT)
                              → /api/agent/*     (steuert Docker-Container via Socket-Mount)
        → LiveKit-Server (WebRTC)  ← Agent-Worker (Python, LiveKit-Agents-SDK)
```

**On-Demand-Modell:** `docker-compose.local.yml` hat die drei Agents unter Compose-**Profiles** (`agent1`, `agent2`, `agent3`, `all-agents`). Ohne Profile werden die Agents **nicht** gestartet. Das Frontend startet/stoppt sie via `docker.sock` auf Knopfdruck. Siehe `frontend/lib/agent-control.ts` und `frontend/app/api/agent/*`.

Der Container bleibt nach dem Start idle und registriert sich als LiveKit-Worker. "Auflegen" im UI = Room verlassen, Container läuft weiter (kein Neustart-Delay beim nächsten Gespräch). "Stop" = Container stoppen (RAM frei).

## Kommandos

```bash
./start.sh setup          # einmalig: Images bauen + Container anlegen
./start.sh                # Infra hochfahren (Frontend + LiveKit + Redis)
./start.sh stop           # alles stoppen
./start.sh logs           # Compose-Logs
./start.sh agent-logs 1   # Logs eines einzelnen Agents (1/2/3)
```

Agent-Hot-Reload (statt Docker):
```bash
cd agents/01-simple-latency && uv sync && uv run python agent.py dev
```

## Wo was liegt

- `agents/0N-<name>/agent.py` — die eigentliche Pipeline (klein halten, didaktisch lesbar)
- `agents/02-appointment-booking/calendar_client.py` — Google-Calendar-Wrapper
- `agents/03-outbound-telephony/prompts.py` — Prompt-Template, getrennt vom Agent
- `frontend/app/page.tsx` — Landing mit den drei Agent-Kacheln
- `frontend/app/agent/[name]/page.tsx` — die Gesprächs-View (verwendet `components/app/app.tsx`)
- `frontend/app/api/agent/{start,stop,status}/route.ts` — Docker-Steuerung
- `frontend/app/api/token/route.ts` — LiveKit-JWT für den Browser
- `docker-compose.local.yml` — Mac/lokales Setup
- `docker-compose.yml` — VPS-Produktion
- `docs/credentials-setup.md` — Provider-Einrichtung (das ist die Quelle der Wahrheit für Zuschauer)
- `docs/vps-deployment.md` — VPS-Deployment inkl. Caddy, Twilio SIP, LiveKit-SIP

## Häufige Pitfalls (aus dem Debugging-Durchlauf)

1. **Alle Agent-Kacheln zeigen "missing"** → `./start.sh setup` wurde übersprungen oder nur `build` gemacht. Die Container müssen via `up --no-start` angelegt werden, sonst kann das Frontend sie nicht starten.
2. **Kachel grün, aber Agent antwortet nicht** → meistens GCP-Permissions. Checkpoints in der Reihenfolge:
   - Vertex AI API in GCP-Console aktiviert?
   - Billing-Account verknüpft?
   - `GOOGLE_CLOUD_PROJECT` ist echte Project-ID, nicht `mein-gcp-projekt`?
   - Service-Account hat `roles/aiplatform.user`?
3. **Deepgram 404 / WSServerHandshakeError** → `DEEPGRAM_BASE_URL` muss `https://api.deepgram.com/v1/listen` sein. Der Hostname `api.eu.deepgram.com` existiert **nicht**; EU-Residency wird per Projekt-Setting im Deepgram-Dashboard konfiguriert.
4. **LiveKit-Connection hängt im Browser stumm** → `/api/token` darf im `serverUrl` nicht die Container-interne URL (`ws://livekit-server:7990`) liefern, sondern `NEXT_PUBLIC_LIVEKIT_URL` (= `ws://localhost:7990`).
5. **Agent 01 braucht `gcp-sa.json` Mount** — nicht nur Agent 02. Steht in `docker-compose.local.yml`.

## Konventionen für Änderungen

- **Didaktische Lesbarkeit > Cleverness.** Die `agent.py`-Dateien sind Teil des Tutorials — lieber eine klare `session = AgentSession(...)`-Initialisierung als raffinierte Abstraktion. Kein Framework-Drumherum.
- **Keine Extras auf der Stage 01.** Simple Latency muss minimal bleiben (~80 Zeilen). Features wandern in 02+.
- **Alle neuen Env-Vars** nach `.env.example` mit einem Kommentar, der DSGVO-Implikationen erklärt.
- **README und `docs/credentials-setup.md`** sind die zwei Einstiegspunkte für Zuschauer. Änderungen, die den Setup-Flow verändern, müssen dort reflektiert sein.
- **Nicht automatisch committen/pushen** ohne explizite User-Bestätigung (shared state).

## Was Claude nicht tun soll

- `.env` oder `secrets/gcp-sa.json` committen. Die `.gitignore` verhindert das — niemals per `git add -f` umgehen.
- Provider durch US-SaaS-Alternativen ersetzen, nur weil sie einfacher aufzusetzen wären. Der DSGVO-Fokus ist der USP.
- Agents automatisch beim `up` starten lassen — dann dauert der erste Start ewig und Zuschauer denken, es sei kaputt.
