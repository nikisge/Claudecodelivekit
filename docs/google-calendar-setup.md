# Google Calendar Setup (für Agent 02)

Agent 02 bucht Termine per Sprache in einem echten Google Kalender. Authentifizierung läuft über einen Service Account — du brauchst keinen OAuth-User-Flow.

## 1. Google Cloud Projekt

1. [console.cloud.google.com](https://console.cloud.google.com) öffnen
2. Neues Projekt anlegen (z. B. `livekit-tutorial`) oder bestehendes nutzen
3. In deiner `.env`:
   ```
   GOOGLE_CLOUD_PROJECT=livekit-tutorial
   ```

## 2. Calendar API aktivieren

1. **APIs & Services → Library → „Google Calendar API" → Enable**

## 3. Service Account anlegen

1. **IAM & Admin → Service Accounts → Create Service Account**
2. Name: `voice-agent-calendar`
3. Rolle: keine projekt-weite nötig (Zugriff regeln wir über Kalender-Share)
4. **Keys → Add Key → Create new key → JSON**
5. JSON herunterladen, im Repo speichern als `secrets/gcp-sa.json` (ins `.gitignore` aufgenommen)

```bash
mkdir -p secrets
mv ~/Downloads/livekit-tutorial-xxxxx.json secrets/gcp-sa.json
```

## 4. Kalender mit dem Service Account teilen

1. Im Service-Account-JSON findest du `client_email`, z. B. `voice-agent-calendar@livekit-tutorial.iam.gserviceaccount.com`. Die brauchen wir gleich.
2. [calendar.google.com](https://calendar.google.com) öffnen
3. Entweder neuen Kalender anlegen (**Weitere Kalender → +**) oder den Hauptkalender nutzen
4. **Einstellungen und Freigabe** → **Für bestimmte Personen oder Gruppen freigeben** → **Personen hinzufügen**
5. Die `client_email` einfügen, Rechte: **Änderungen an Terminen vornehmen**
6. Kalender-ID kopieren (unter „Kalender integrieren"), z. B. `primary` oder `abc123@group.calendar.google.com`

In `.env`:
```
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
GOOGLE_CALENDAR_ID=primary
```

## 5. Vertex AI (gleiches Projekt, für Agent 01)

Agent 01 nutzt Gemini 2.5 Flash Lite. Wenn du Vertex AI im gleichen GCP-Projekt aktivierst:

1. **APIs & Services → Library → „Vertex AI API" → Enable**
2. Dem gleichen Service Account im **IAM** die Rolle `Vertex AI User` geben
3. In `.env`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp-sa.json
   GOOGLE_CLOUD_LOCATION=europe-west4
   GEMINI_MODEL=gemini-2.5-flash-lite
   ```

Die gleiche JSON-Datei wird also von beiden Agents genutzt.

## Test

```bash
cd agents/02-appointment-booking
uv sync
uv run python -c "
from calendar_client import CalendarClient
import os
c = CalendarClient(os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH'), os.getenv('GOOGLE_CALENDAR_ID'))
print(c.list_free_slots('2026-04-22'))
"
```

Sollte eine Liste freier Slots (oder leere Liste am Wochenende) ausgeben.

## DSGVO-Hinweis

Google Calendar läuft auf Google-Infrastruktur. Wenn dein Google-Workspace-Account in der EU registriert ist, gilt Google Workspace EU-Data-Residency. Für volle Kontrolle ohne Google-Bindung wäre Nextcloud Calendar mit CalDAV-Protokoll eine Alternative — das ist aber bewusst nicht Teil dieses Tutorials (Fokus bleibt auf dem LiveKit-Konzept, nicht auf alternativer Kalender-Infra).

Bei privaten Gmail-Accounts (nicht Workspace) greift EU-Data-Residency nicht. Für Produktivbetrieb mit Kundendaten: Workspace-Account mit aktiver EU-Data-Region nutzen.
