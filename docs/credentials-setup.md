# Credentials einrichten — Schritt für Schritt

Dieser Leitfaden zeigt, welche Accounts/Keys du brauchst und wie du sie DSGVO-konform konfigurierst. Reihenfolge ist so gewählt, dass du nach jedem Abschnitt den zugehörigen Agent testen kannst.

Kurzfassung:

| Agent | Brauchst du | Abschnitt |
|---|---|---|
| 01 Simple Latency | Google Cloud, Deepgram, Cartesia | 1, 3, 4 |
| 02 Appointment Booking | Azure OpenAI, Deepgram, ElevenLabs, Google Calendar | 2, 3, 5, 6 |
| 03 Outbound Telephony | Azure OpenAI, Deepgram, ElevenLabs, Twilio, VPS | 2, 3, 5, 7 |

Alle Keys landen in der `.env` (aus `.env.example` kopieren: `cp .env.example .env`).

---

## 1. Google Cloud (Vertex AI / Gemini — für Agent 01)

Agent 01 nutzt Gemini über Vertex AI in der EU-Region. Du brauchst ein GCP-Projekt, ein Service-Account-JSON und drei aktivierte Sachen.

### 1.1 Projekt + Service Account

1. In der [GCP-Console](https://console.cloud.google.com/) ein Projekt anlegen (oder vorhandenes nutzen). Notiere die **Project-ID** (nicht den Namen — die ID steht oben in der Projekt-Auswahl).
2. Links im Menü → **IAM & Admin → Service Accounts** → **Create Service Account**. Name z.B. `livekit-voice-agent`.
3. Rolle hinzufügen: **Vertex AI User** (`roles/aiplatform.user`). Für Agent 02 zusätzlich nichts — Calendar regelt sich separat (Abschnitt 6).
4. Bei dem Service-Account → Tab **Keys** → **Add Key → Create new key → JSON**. Die Datei landet in deinen Downloads.
5. Datei umbenennen zu `gcp-sa.json` und in `secrets/gcp-sa.json` im Repo-Root ablegen.

### 1.2 Vertex AI API aktivieren

Ohne das gibt's `403 PERMISSION_DENIED / CONSUMER_INVALID`, selbst mit gültigem Service Account:

https://console.cloud.google.com/apis/library/aiplatform.googleapis.com

→ Dein Projekt oben auswählen → **Enable**.

### 1.3 Billing aktivieren

Vertex AI ist nicht kostenlos und funktioniert ohne verknüpftes Rechnungskonto **gar nicht** (auch nicht im Free Tier):

https://console.cloud.google.com/billing/linkedaccount

→ Projekt wählen → Billing-Account verknüpfen. Eine Karte oder SEPA-Lastschrift reicht.

### 1.4 In `.env` eintragen

```env
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-sa.json
GOOGLE_CLOUD_PROJECT=deine-project-id
GOOGLE_CLOUD_LOCATION=europe-west4
GEMINI_MODEL=gemini-2.5-flash-lite
```

**Wichtig:** `GOOGLE_CLOUD_PROJECT` muss die **Project-ID** sein (z.B. `mein-projekt-123456`), nicht der Anzeigename.

---

## 2. Azure OpenAI (für Agent 02 + 03)

DSGVO-wichtig: **EU Data Zone Standard** deployen, nicht Global Standard.

1. Im [Azure Portal](https://portal.azure.com/) eine **Azure OpenAI Resource** anlegen. Region: `swedencentral`.
2. Im [Azure AI Foundry](https://ai.azure.com/) → Deployments → **Create** → Modell `gpt-4.1-mini` → Deployment-Type: **EU Data Zone Standard** (nicht Global!).
3. Aus der Resource:
   - **Keys and Endpoint** → Key 1 → `AZURE_OPENAI_API_KEY`
   - Endpoint-URL (https://…openai.azure.com) → `AZURE_OPENAI_ENDPOINT`

```env
AZURE_OPENAI_API_KEY=<dein-key>
AZURE_OPENAI_ENDPOINT=https://<deine-resource>.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
```

---

## 3. Deepgram (STT — für alle Agents)

DSGVO: EU-Residency wird nicht über eine separate URL gemacht, sondern im Dashboard pro Projekt.

1. Account auf [deepgram.com](https://deepgram.com) anlegen.
2. Neues Projekt → **Settings → Region: EU** (Frankfurt). Diesen Schritt **nicht vergessen**, sonst landen Audiodaten in den USA.
3. **API Keys → Create a New API Key** → Rolle "Member" reicht.

```env
DEEPGRAM_API_KEY=<dein-key>
DEEPGRAM_BASE_URL=https://api.deepgram.com/v1/listen
```

**Nicht** `api.eu.deepgram.com` eintragen — diesen Endpoint gibt es nicht. Der globale Endpoint routet automatisch zu EU, wenn dein Projekt EU-Region ist.

---

## 4. Cartesia (TTS — für Agent 01)

1. Account auf [cartesia.ai](https://cartesia.ai) anlegen.
2. **API Keys → Create** → kopieren.
3. Für DSGVO: Im Account-Setting **Zero-Retention** aktivieren und den DPA unterzeichnen (Support anschreiben, dauert 1–2 Tage).
4. Unter [play.cartesia.ai/voices](https://play.cartesia.ai/voices) eine **deutsche Stimme** aus dem `sonic-multilingual`-Katalog suchen (nach "German" filtern, Probe anhören). Voice-ID kopieren.

```env
CARTESIA_API_KEY=<dein-key>
CARTESIA_VOICE_ID=<voice-id-aus-library>
```

**Achtung:** Wenn du eine englische Stimme nimmst, spricht der Agent deutschen Text mit US-Akzent — prüfe die Voice-ID vor dem Einchecken.

---

## 5. ElevenLabs (TTS — für Agent 02 + 03)

Default-Stimme für dieses Repo ist **"Johanna"** (deutsch).

1. Account auf [elevenlabs.io](https://elevenlabs.io) — DSGVO: für echte Produktion braucht's den **Enterprise Plan mit EU-Residency**, andernfalls Data-Transfer in US.
2. In **Voice Library** nach "Johanna" suchen (oder andere deutsche Stimme) → "Add to VoiceLab" → Voice-ID kopieren.
3. **Profile Settings → API Keys**.

```env
ELEVENLABS_API_KEY=<dein-key>
ELEVEN_VOICE_ID=<voice-id>
```

---

## 6. Google Calendar (für Agent 02)

Der Termin-Assistent schreibt in einen echten Google Calendar. Das läuft über den **gleichen Service Account** wie Vertex AI (Abschnitt 1) — du musst ihm nur Zugriff auf den Kalender geben.

1. Die **Service-Account-E-Mail** kopieren (sieht aus wie `livekit-voice-agent@<project-id>.iam.gserviceaccount.com`). Steht im `gcp-sa.json` unter `client_email`, oder in der GCP-Console bei dem Service Account.
2. Google Calendar öffnen ([calendar.google.com](https://calendar.google.com)).
3. Links bei deinem gewünschten Kalender → Drei-Punkte-Menü → **Settings and sharing**.
4. Scroll zu **Share with specific people or groups → Add people** → Service-Account-E-Mail einfügen → Berechtigung auf **Make changes to events** setzen.
5. **Calendar ID** kopieren (weiter unten auf der gleichen Seite, z.B. `dein-kalender@group.calendar.google.com`). Für deinen privaten Kalender reicht `primary`.

```env
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
GOOGLE_CALENDAR_ID=primary
```

**Häufiger Fehler:** Agent bekommt `403` auf Calendar-API → Service-Account-E-Mail nicht (oder mit falscher Berechtigung) geteilt.

---

## 7. Twilio SIP (Agent 03 — nur VPS)

Lokal nicht sinnvoll testbar. Für das VPS-Setup siehe `docs/twilio-setup.md` und `docs/vps-deployment.md`.

---

## 8. LiveKit-Keys (lokal generieren)

Keine externe Registrierung nötig — Keys werden lokal erzeugt:

```bash
./scripts/generate-keys.sh
```

Das Skript schreibt `LIVEKIT_API_KEY` und `LIVEKIT_API_SECRET` in deine `.env`.

---

## Sanity-Check vor dem ersten Start

Minimal für Agent 01 gesetzt?

```bash
grep -E '^(LIVEKIT_API_KEY|LIVEKIT_API_SECRET|DEEPGRAM_API_KEY|CARTESIA_API_KEY|CARTESIA_VOICE_ID|GOOGLE_CLOUD_PROJECT)=' .env | awk -F= '{print $1, ($2=="" ? "LEER!" : "ok")}'
```

Alles `ok`? Dann:

```bash
./start.sh setup   # einmalig, baut Images + legt Container an (~5 Min)
./start.sh         # startet LiveKit + Frontend
```

Browser: http://localhost:3000 → Simple-Latency → "Start" → "Öffnen" → reden.

## Die drei häufigsten Probleme beim ersten Start

1. **Alle Kacheln zeigen "missing"** → `./start.sh setup` wurde übersprungen. Einmal nachholen.
2. **Kachel grün, aber Agent antwortet nicht** → fast immer GCP: Vertex AI API nicht aktiviert, Billing fehlt, oder `GOOGLE_CLOUD_PROJECT` ist noch auf `mein-gcp-projekt`. Abschnitt 1.2/1.3/1.4 durchgehen.
3. **"Deepgram 404"** → `DEEPGRAM_BASE_URL` ist falsch. Muss `https://api.deepgram.com/v1/listen` sein, nicht `api.eu.deepgram.com` (existiert nicht).
