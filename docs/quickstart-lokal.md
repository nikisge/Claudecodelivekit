# Quickstart — lokal auf dem Mac

Setup in ~10 Minuten. Ziel: du kannst im Browser mit Agent 1 und Agent 2 reden.
Agent 3 (Outbound) funktioniert lokal nur mit ngrok-Umweg — den Teil deployen wir direkt auf den VPS.

## Voraussetzungen

- macOS mit **Docker Desktop** installiert und gestartet
- **Python 3.11+** (`python3 --version` prüfen)
- **uv** oder **pip** für Python-Deps (`brew install uv` empfohlen)
- **pnpm** für Frontend (`brew install pnpm` oder `corepack enable`)
- API-Accounts bei:
  - Google Cloud (für Vertex AI + Calendar, Service Accounts)
  - Microsoft Azure (OpenAI, EU Data Zone)
  - Azure Speech (EU-Region für STT/TTS)
  - Deepgram (EU-Endpoint für Agent 01)

## Schritte

### 1. Repo klonen und Keys generieren

```bash
git clone <dein-fork> livekit-voice-agents-de
cd livekit-voice-agents-de
./scripts/generate-keys.sh
```

Erstellt `.env` und trägt frische LiveKit API-Keys ein.

### 2. Provider-Keys in `.env` eintragen

Öffne `.env` und fülle aus:

```bash
# Google Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp-sa.json
GOOGLE_CLOUD_PROJECT=dein-gcp-projekt
GOOGLE_CLOUD_LOCATION=europe-west4

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://dein-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini

# Azure Speech (EU)
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=swedencentral
AZURE_SPEECH_LANGUAGE=de-DE
AZURE_SPEECH_VOICE=de-DE-SeraphinaMultilingualNeural

# Deepgram (EU, Agent 01)
DEEPGRAM_API_KEY=...
DEEPGRAM_BASE_URL=https://api.eu.deepgram.com
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=de

# Google Calendar (für Agent 02)
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
GOOGLE_CALENDAR_ID=primary
```

Details zu jedem Provider: `docs/dsgvo-compliance.md` und `docs/google-calendar-setup.md`.

### 3. Infrastruktur starten

```bash
./start.sh setup
./start.sh
```

Check: `curl http://localhost:7990` gibt `404 page not found` zurück — das ist OK, der Server antwortet.

### 4. Frontend öffnen

```bash
open http://localhost:3000
```

Du siehst die Agent-Übersicht mit drei Kacheln. Die Agent-Container startest und stoppst du direkt im Browser.

### 5. Agent 1 starten

In einem **zweiten Terminal**:

```bash
cd agents/01-simple-latency
uv sync
uv run python agent.py dev
```

Klicke im Browser auf **Simple Latency**, erlaube Mikrofon, klicke **Gespräch starten** → der Agent begrüßt dich.

### 6. Agent 2 starten (separat)

In einem **dritten Terminal**:

```bash
cd agents/02-appointment-booking
uv sync
uv run python agent.py dev
```

Im Browser auf **Termin-Assistent** klicken. Sprich: „Ich möchte am Freitag um 14 Uhr einen Termin buchen, mein Name ist Max Mustermann." Der Agent antwortet, ruft `list_free_slots` und `book_appointment` auf, und der Termin erscheint im konfigurierten Google Kalender.

## Troubleshooting

**Browser: „Token endpoint error"** → lokal muss das Frontend `NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7990` nutzen. Im Docker-Setup ist das bereits in `docker-compose.local.yml` gesetzt.

**Agent joint den Room nicht** → `docker compose logs livekit-server` anschauen. Häufig: LIVEKIT_API_KEY stimmt zwischen Server und Agent nicht überein.

**Agent 01 versteht nichts** → `DEEPGRAM_API_KEY` und `DEEPGRAM_BASE_URL=https://api.eu.deepgram.com` prüfen. Für Deutsch `DEEPGRAM_LANGUAGE=de` setzen.

**Agent 02/03 verstehen nichts** → `AZURE_SPEECH_KEY` und `AZURE_SPEECH_REGION` prüfen. Key und Region müssen zur gleichen Speech-Resource gehören.

**TTS bleibt stumm** → `AZURE_SPEECH_VOICE` prüfen. Für Deutsch z. B. `de-DE-SeraphinaMultilingualNeural`, `de-DE-FlorianMultilingualNeural`, `de-DE-KatjaNeural`.

**Azure: 401** → Deployment in Azure Portal muss genau so heißen wie `AZURE_OPENAI_DEPLOYMENT`. Prüfe außerdem `AZURE_OPENAI_API_VERSION`.
