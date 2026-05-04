# Credentials einrichten — Schritt für Schritt

Alle Provider-Accounts + Keys für die drei Agents. Reihenfolge so gewählt, dass du nach jedem Abschnitt testen kannst.

## Was brauchst du wofür?

| Agent | Services |
|---|---|
| **01 Simple Latency** | Azure OpenAI · Azure Speech *(optional: Deepgram EU + Vertex AI)* |
| **02 Termin-Assistent** | Azure OpenAI · Azure Speech · Google Calendar |
| **03 Outbound-Telephony** | Azure OpenAI · Azure Speech · Twilio (nur auf VPS) |

## Quick-Links

| Provider | Dashboard | Was abholen |
|---|---|---|
| Google Cloud | [console.cloud.google.com](https://console.cloud.google.com/) | Project-ID, Service-Account-JSON |
| Azure OpenAI | [portal.azure.com](https://portal.azure.com/#create/Microsoft.CognitiveServicesOpenAI) | Endpoint + API-Key |
| Azure Speech | [portal.azure.com](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices) | Speech-Key + Region |
| Azure AI Foundry | [ai.azure.com](https://ai.azure.com/) | Modell-Deployment |
| Deepgram | [console.deepgram.com](https://console.deepgram.com/) | STT-Key + EU-Endpoint |
| Cartesia/ElevenLabs optional | Anbieter-Konsole | Alternative TTS nur mit Enterprise/EU/Zero-Retention |
| Twilio | [console.twilio.com](https://console.twilio.com/) | Trunk + Nummer (nur VPS) |

`cp .env.example .env` und unten die Keys nacheinander eintragen.

---

## 1. Google Cloud (Calendar + optional Vertex AI)

Pflicht nur für Agent 02 (Calendar). Vertex AI ist Agent-01-Alternative; wer beim Azure-Default bleibt, kann diesen Abschnitt für Agent 01 überspringen.

> **Warum Service Account statt OAuth2 (wie in n8n)?** Der Agent läuft in einem Docker-Container ohne Browser, ein OAuth2-Redirect-Flow wäre umständlich. Außerdem zwingt Google OAuth2-Apps mit Calendar-Scope in den Testing-Mode (100 User max) oder eine wochenlange App-Verification. Für den 1-Kalender-Fall ist SA deutlich einfacher. Multi-Tenant-Szenarien (mehrere Kunden mit eigenem Kalender) wären ein Grund, OAuth2 zu nutzen — für dieses Tutorial nicht relevant.

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

## 3. Azure Speech (STT + TTS — alle Agents)

**DSGVO:** Speech-Resource in einer EU-Region anlegen, z. B. `swedencentral`, `germanywestcentral`, `westeurope` oder `francecentral`. Microsoft dokumentiert, dass Azure Speech Daten nicht außerhalb der Region der Speech-Resource speichert oder verarbeitet.

1. Resource anlegen: https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices
2. Region wählen: z. B. `swedencentral` (passt gut zu Azure OpenAI Sweden Central).
3. **Keys and Endpoint** → Key 1 kopieren.
4. Stimme wählen. Gute deutsche Defaults:
   - `de-DE-SeraphinaMultilingualNeural` (weiblich, modern)
   - `de-DE-FlorianMultilingualNeural` (männlich, modern)
   - `de-DE-KatjaNeural` (weiblich, stabil)
   - `de-DE-ConradNeural` (männlich, stabil)

```env
AZURE_SPEECH_KEY=<key>
AZURE_SPEECH_REGION=swedencentral
AZURE_SPEECH_LANGUAGE=de-DE
AZURE_SPEECH_VOICE=de-DE-SeraphinaMultilingualNeural
```

---

## 4. Deepgram (optional: STT-Alternative für Agent 01)

**DSGVO:** Für EU-Verarbeitung den Deepgram-EU-Endpoint `https://api.eu.deepgram.com` nutzen. Laut Deepgram-Doku funktionieren bestehende API-Keys auch mit diesem Endpoint.

1. Account: https://deepgram.com/
2. API Keys: https://console.deepgram.com/ → **API Keys → Create**.
3. Rolle "Member" reicht für dieses Projekt.

```env
DEEPGRAM_API_KEY=<key>
DEEPGRAM_BASE_URL=https://api.eu.deepgram.com
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=de
```

---

## 5. Cartesia (optional: TTS-Alternative)

1. Account: https://cartesia.ai/
2. [play.cartesia.ai](https://play.cartesia.ai/) → **API Keys → Create**.
3. **DSGVO:** Nur als Enterprise-/Custom-Vertragsoption sauber fürs EU-only-Video verwenden. Zero-Retention im Account aktivieren, DPA unterzeichnen, EU-Hosting schriftlich oder im Account bestätigen lassen.
4. Voice suchen: https://play.cartesia.ai/voices → nach "German" filtern, Probe anhören → **Voice-ID** kopieren (wichtig: deutsche Stimme, sonst spricht der Agent mit US-Akzent).

```env
CARTESIA_API_KEY=<key>
CARTESIA_VOICE_ID=<voice-id>
```

---

## 6. ElevenLabs (optional: TTS-Alternative)

Beispielstimme: **"Johanna"** (deutsch). Nur als Alternative zum Azure-Speech-Default verwenden.

1. Account: https://elevenlabs.io/ — **DSGVO:** Enterprise-Plan mit EU-Residency. EU-API läuft über `https://api.eu.residency.elevenlabs.io`, mit eigenem EU-Workspace/API-Key. Zero-Retention zusätzlich aktivieren.
2. API-Key: https://elevenlabs.io/app/settings/api-keys
3. Voice Library → "Johanna" suchen → **Add to VoiceLab** → Voice-ID kopieren.

```env
ELEVENLABS_API_KEY=<key>
ELEVEN_VOICE_ID=<voice-id>
```

---

## 7. Twilio (Agent 03 — nur auf VPS)

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

## 8. LiveKit-Keys (lokal generieren)

```bash
./scripts/generate-keys.sh
```

Schreibt `LIVEKIT_API_KEY` und `LIVEKIT_API_SECRET` automatisch in deine `.env`.

---

## Sanity-Check vor dem ersten Start

Minimum für Agent 01 gesetzt?

```bash
grep -E '^(LIVEKIT_API_KEY|LIVEKIT_API_SECRET|AZURE_SPEECH_KEY|AZURE_SPEECH_REGION|GOOGLE_CLOUD_PROJECT)=' .env \
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
3. **Azure Speech 401** → `AZURE_SPEECH_KEY` und `AZURE_SPEECH_REGION` müssen zur gleichen Speech-Resource gehören.
4. **Agent 02 kann keinen Termin buchen (403)** → Service-Account-E-Mail nicht im Kalender freigegeben, oder Calendar API nicht aktiviert.
