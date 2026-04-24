# Credentials einrichten — Schritt für Schritt

Alle Provider-Accounts + Keys für die drei Agents. Reihenfolge so gewählt, dass du nach jedem Abschnitt testen kannst.

## Was brauchst du wofür?

| Agent | Services |
|---|---|
| **01 Simple Latency** | Google Cloud (Vertex AI) · Deepgram · Cartesia |
| **02 Termin-Assistent** | Azure OpenAI · Deepgram · ElevenLabs · Google Calendar |
| **03 Outbound-Telephony** | Azure OpenAI · Deepgram · ElevenLabs · Twilio (nur auf VPS) |

## Quick-Links

| Provider | Dashboard | Was abholen |
|---|---|---|
| Google Cloud | [console.cloud.google.com](https://console.cloud.google.com/) | Project-ID, Service-Account-JSON |
| Azure OpenAI | [portal.azure.com](https://portal.azure.com/#create/Microsoft.CognitiveServicesOpenAI) | Endpoint + API-Key |
| Azure AI Foundry | [ai.azure.com](https://ai.azure.com/) | Modell-Deployment |
| Deepgram | [console.deepgram.com](https://console.deepgram.com/) | API-Key + EU-Region im Projekt |
| Cartesia | [play.cartesia.ai](https://play.cartesia.ai/) | API-Key + Voice-ID |
| ElevenLabs | [elevenlabs.io/app](https://elevenlabs.io/app/settings/api-keys) | API-Key + Voice-ID |
| Twilio | [console.twilio.com](https://console.twilio.com/) | Trunk + Nummer (nur VPS) |

`cp .env.example .env` und unten die Keys nacheinander eintragen.

---

## 1. Google Cloud (Vertex AI + Calendar)

Ein einziger Service Account für beides — Vertex AI (Agent 01) und Calendar (Agent 02).

### 1.1 Projekt + Service Account
1. In [GCP Console](https://console.cloud.google.com/) Projekt anlegen. **Project-ID** notieren (die ID oben in der Projekt-Auswahl, nicht der Anzeigename).
2. [IAM → Service Accounts → Create](https://console.cloud.google.com/iam-admin/serviceaccounts) → Name: `livekit-voice-agent`.
3. Rolle: **Vertex AI User** (`roles/aiplatform.user`).
4. Beim erstellten Service Account → Tab **Keys → Add Key → JSON** → Datei als `secrets/gcp-sa.json` speichern.

### 1.2 APIs aktivieren (wichtig — sonst 403 CONSUMER_INVALID)

- **Vertex AI API** aktivieren: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
- **Google Calendar API** aktivieren: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com

### 1.3 Billing verknüpfen (sonst 403 egal was)

https://console.cloud.google.com/billing/linkedaccount → Billing-Account zuordnen. Karte oder SEPA reicht.

### 1.4 Kalender mit Service Account teilen (für Agent 02)

1. Aus `secrets/gcp-sa.json` das Feld `client_email` kopieren (z.B. `livekit-voice-agent@<project-id>.iam.gserviceaccount.com`).
2. [calendar.google.com](https://calendar.google.com/) öffnen → gewünschter Kalender → Drei-Punkte-Menü → **Einstellungen und Freigabe**.
3. **Für bestimmte Personen oder Gruppen freigeben → Hinzufügen** → `client_email` einfügen → Berechtigung: **Änderungen an Terminen vornehmen**.
4. **Kalender-ID** von der gleichen Seite kopieren (`primary` für deinen Hauptkalender, sonst `xxx@group.calendar.google.com`).

### 1.5 `.env`

```env
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-sa.json
GOOGLE_CLOUD_PROJECT=deine-project-id
GOOGLE_CLOUD_LOCATION=europe-west4
GEMINI_MODEL=gemini-2.5-flash-lite
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
GOOGLE_CALENDAR_ID=primary
```

> Details zu Calendar: [docs/google-calendar-setup.md](./google-calendar-setup.md)

---

## 2. Azure OpenAI (Agent 02 + 03)

**DSGVO:** zwingend "EU Data Zone Standard" deployen, **nicht** "Global Standard".

1. Resource anlegen: https://portal.azure.com/#create/Microsoft.CognitiveServicesOpenAI → Region `swedencentral`.
2. In [Azure AI Foundry](https://ai.azure.com/) → **Deployments → Create** → Modell `gpt-4.1-mini` → Deployment-Typ: **EU Data Zone Standard**.
3. In der Azure-Resource → **Keys and Endpoint** → Key 1 + Endpoint-URL abholen.

```env
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=https://<deine-resource>.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
```

---

## 3. Deepgram (STT — alle Agents)

**DSGVO:** EU-Residency wird **nicht** per URL gesetzt (ein `api.eu.deepgram.com`-Hostname existiert nicht) — sondern im Dashboard pro Projekt.

1. Account: https://deepgram.com/
2. Projekt-Settings: https://console.deepgram.com/ → **Settings → Region: EU**.
3. **API Keys → Create** (Rolle "Member" reicht).

```env
DEEPGRAM_API_KEY=<key>
DEEPGRAM_BASE_URL=https://api.deepgram.com/v1/listen
```

---

## 4. Cartesia (TTS — Agent 01)

1. Account: https://cartesia.ai/
2. [play.cartesia.ai](https://play.cartesia.ai/) → **API Keys → Create**.
3. **DSGVO:** Zero-Retention im Account-Setting aktivieren + DPA unterzeichnen (Support anschreiben).
4. Voice suchen: https://play.cartesia.ai/voices → nach "German" filtern, Probe anhören → **Voice-ID** kopieren (wichtig: deutsche Stimme, sonst spricht der Agent mit US-Akzent).

```env
CARTESIA_API_KEY=<key>
CARTESIA_VOICE_ID=<voice-id>
```

---

## 5. ElevenLabs (TTS — Agent 02 + 03)

Default-Stimme: **"Johanna"** (deutsch).

1. Account: https://elevenlabs.io/ — **DSGVO:** Enterprise-Plan mit EU-Residency (sonst Data-Transfer in US).
2. API-Key: https://elevenlabs.io/app/settings/api-keys
3. Voice Library → "Johanna" suchen → **Add to VoiceLab** → Voice-ID kopieren.

```env
ELEVENLABS_API_KEY=<key>
ELEVEN_VOICE_ID=<voice-id>
```

---

## 6. Twilio (Agent 03 — nur auf VPS)

Lokal nicht sinnvoll testbar (Twilio muss per SIP zum öffentlich erreichbaren LiveKit verbinden). Kurzfassung:

1. [console.twilio.com](https://console.twilio.com/) → Account anlegen, Zahlungsmethode hinterlegen (kein Free-Trial für SIP).
2. **Region auf EU stellen** für DSGVO: Console-Header → Region-Dropdown → `eu1` (Dublin) oder `de1` (Frankfurt). [Twilio-Regions-Doku](https://www.twilio.com/docs/global-infrastructure)
3. **Phone Numbers → Buy a Number** → Voice-Capability ✔, Region DE/AT/CH.
4. **Elastic SIP Trunking → Trunks → Create** → `livekit-tutorial-trunk`.
   - **Termination URI** (z.B. `voiceagents.pstn.twilio.com`) → `TWILIO_SIP_TRUNK_URI`
   - **Credential List** (Username/Passwort) anlegen → **das** sind `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` (nicht die Account-Top-Level-Tokens!).
   - **Numbers** → gekaufte Nummer zuordnen.
5. Auf dem VPS: `python3 scripts/setup-sip.py` → liefert `LIVEKIT_OUTBOUND_TRUNK_ID` zurück, in `.env` eintragen.
6. **DPA** unterzeichnen: Console → Privacy & Compliance.

```env
TWILIO_SIP_TRUNK_URI=sip:<trunk>.pstn.twilio.com
TWILIO_ACCOUNT_SID=<trunk-credential-user>
TWILIO_AUTH_TOKEN=<trunk-credential-pw>
TWILIO_PHONE_NUMBER=+49...
LIVEKIT_OUTBOUND_TRUNK_ID=ST_xxx
```

> **Vollständiges Setup inkl. Firewall/NAT-Troubleshooting:** [docs/twilio-setup.md](./twilio-setup.md)

---

## 7. LiveKit-Keys (lokal generieren)

```bash
./scripts/generate-keys.sh
```

Schreibt `LIVEKIT_API_KEY` und `LIVEKIT_API_SECRET` automatisch in deine `.env`.

---

## Sanity-Check vor dem ersten Start

Minimum für Agent 01 gesetzt?

```bash
grep -E '^(LIVEKIT_API_KEY|LIVEKIT_API_SECRET|DEEPGRAM_API_KEY|CARTESIA_API_KEY|CARTESIA_VOICE_ID|GOOGLE_CLOUD_PROJECT)=' .env \
  | awk -F= '{print $1, ($2=="" ? "LEER!" : "ok")}'
```

Alles `ok` und `GOOGLE_CLOUD_PROJECT` ≠ `mein-gcp-projekt`? Dann los:

```bash
./start.sh setup   # einmalig: Images bauen + Container anlegen (~5 Min)
./start.sh         # Infra starten
```

→ http://localhost:3000 → Agent auswählen → "Start" → "Öffnen" → reden.

## Häufigste Startprobleme

1. **Alle Kacheln "missing"** → `./start.sh setup` übersprungen.
2. **Kachel grün, keine Antwort** → fast immer GCP: Vertex AI API nicht aktiv, Billing fehlt, oder Project-ID steht noch auf `mein-gcp-projekt`.
3. **Deepgram 404** → `DEEPGRAM_BASE_URL` ist falsch. Korrekt: `https://api.deepgram.com/v1/listen`.
4. **Agent 02 kann keinen Termin buchen (403)** → Service-Account-E-Mail nicht im Kalender freigegeben, oder Calendar API nicht aktiviert.
