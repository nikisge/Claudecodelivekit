# Agent 02 — Appointment Booking

Voice-Agent mit Function Calling gegen die echte Google Calendar API. Zeigt, wie man
Tools mit LiveKit baut und einen Multi-Turn-Flow ("Finde meinen Termin → Verschiebe
ihn → Bestätige") in wenigen Zeilen umsetzt.

## Tools

| Tool | Zweck |
|---|---|
| `list_free_slots(date)` | Zeigt freie 30-Min-Slots an einem Werktag |
| `book_appointment(start_iso, name, duration_min?, notes?)` | Legt Kalender-Event an |
| `find_my_appointments(name)` | Sucht Termine per Namens-Substring |
| `reschedule_appointment(event_id, new_start_iso)` | Verschiebt Termin |
| `cancel_appointment(event_id)` | Sagt Termin ab |

## Setup

1. Google-Cloud-Service-Account anlegen und JSON runterladen → `secrets/gcp-sa.json`
2. Den gewünschten Kalender mit der Service-Account-E-Mail teilen (Schreibrechte)
3. In `.env`:
   ```
   GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
   GOOGLE_CALENDAR_ID=<kalender-ID, z. B. user@workspace.de oder primary>
   ```

Vollständige Schritt-für-Schritt-Anleitung: `docs/google-calendar-setup.md`.

## Lokal starten

```bash
cd agents/02-appointment-booking
uv sync
uv run python agent.py dev
```

## Warum Gemini 2.5 Flash via Vertex AI?

- Schnelles Tool-Calling (geringere Latenz als GPT-4o, mehr Intelligenz als GPT-3.5)
- EU Data Zone in Azure Sweden Central → DSGVO-dokumentierbar
- GPT-4.1-mini kann in der Regel Datumsangaben aus Sprache ("nächsten Dienstag um 15 Uhr") korrekt in ISO-Format umsetzen, was für die Tool-Args wichtig ist

## DSGVO

- **Vertex AI:** EU-Region wie `europe-west4` setzen
- **Azure Speech:** Speech-Resource in EU-Region für STT/TTS; ElevenLabs nur optional mit Enterprise EU Residency + Zero-Retention
- **Google Calendar:** Daten liegen bei Google. Wenn dein Google Workspace in der EU registriert ist, greift die EU-Data-Residency von Google Workspace. Für volle Kontrolle → Nextcloud Calendar mit CalDAV (out of scope dieses Tutorials)
