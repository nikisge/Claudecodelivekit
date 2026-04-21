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
  - Deepgram (EU-Endpoint)
  - Cartesia (Zero-Retention aktivieren)
  - ElevenLabs (Voice „Johanna" in deinem Workspace)

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

# Deepgram (EU)
DEEPGRAM_API_KEY=...

# Cartesia
CARTESIA_API_KEY=...
CARTESIA_VOICE_ID=<aus Voice Library kopiert, deutsche Stimme>

# ElevenLabs
ELEVENLABS_API_KEY=...
ELEVEN_VOICE_ID=<Voice-ID von Johanna>

# Google Calendar (für Agent 02)
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
GOOGLE_CALENDAR_ID=primary
```

Details zu jedem Provider: `docs/dsgvo-compliance.md` und `docs/google-calendar-setup.md`.

### 3. LiveKit-Server + Redis starten

```bash
docker compose -f docker-compose.local.yml up -d redis livekit-server
```

Check: `curl http://localhost:7880` gibt `404 page not found` zurück — das ist OK, der Server antwortet.

### 4. Frontend starten

```bash
cd frontend
pnpm install
pnpm dev
```

→ Öffne http://localhost:3000. Du siehst die Landing-Page mit drei Kacheln.

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

**Browser: „Token endpoint error"** → prüfe `NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880` und `LIVEKIT_URL=ws://localhost:7880` in der Frontend-ENV.

**Agent joint den Room nicht** → `docker compose logs livekit-server` anschauen. Häufig: LIVEKIT_API_KEY stimmt zwischen Server und Agent nicht überein.

**STT versteht nichts** → Deepgram-Key prüfen, `DEEPGRAM_BASE_URL=https://api.eu.deepgram.com` gesetzt? Sample-Rate des Browser-Mikrofons testen.

**Cartesia: „Voice not found"** → in der Cartesia-Konsole unter Voices eine deutsche Stimme auswählen, Voice-ID kopieren nach `CARTESIA_VOICE_ID`.

**Azure: 401** → Deployment in Azure Portal muss genau so heißen wie `AZURE_OPENAI_DEPLOYMENT`. Prüfe außerdem `AZURE_OPENAI_API_VERSION`.
