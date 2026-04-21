"""
Dünner Wrapper um die Google Calendar API. Authentifiziert sich via Service Account
(JSON-Credentials-Datei), arbeitet standardmäßig in Europe/Berlin.

Konzept für dieses Tutorial:
- Ein fester Kalender (GOOGLE_CALENDAR_ID), mit dem der Service-Account geteilt ist
- Arbeitszeiten Mo–Fr 9–17 Uhr, 30-Minuten-Slots
- Termine werden mit dem Namen des Kunden im Titel angelegt → find_appointments kann später
  per Namens-Substring suchen (ohne dass der Kunde seine Event-ID kennen muss)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

BERLIN = ZoneInfo("Europe/Berlin")
WORKING_HOURS = (9, 17)
SLOT_MINUTES = 30
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarClient:
    def __init__(self, service_account_path: str, calendar_id: str) -> None:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        self.calendar_id = calendar_id

    def list_free_slots(self, date: str) -> list[str]:
        """Gibt ISO-Startzeiten freier 30-Min-Slots an einem Werktag zurück (date=YYYY-MM-DD)."""
        day = datetime.fromisoformat(date).replace(tzinfo=BERLIN)
        if day.weekday() >= 5:  # Samstag/Sonntag
            return []

        start = day.replace(hour=WORKING_HOURS[0], minute=0, second=0, microsecond=0)
        end = day.replace(hour=WORKING_HOURS[1], minute=0, second=0, microsecond=0)

        busy = self._busy_ranges(start, end)

        free: list[str] = []
        cursor = start
        while cursor + timedelta(minutes=SLOT_MINUTES) <= end:
            slot_end = cursor + timedelta(minutes=SLOT_MINUTES)
            if not any(cursor < b_end and slot_end > b_start for b_start, b_end in busy):
                free.append(cursor.isoformat())
            cursor += timedelta(minutes=SLOT_MINUTES)
        return free

    def book(self, start_iso: str, duration_min: int, name: str, notes: str = "") -> dict:
        start_dt = datetime.fromisoformat(start_iso)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=BERLIN)
        end_dt = start_dt + timedelta(minutes=duration_min)

        event = {
            "summary": f"Termin mit {name}",
            "description": notes,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Berlin"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Berlin"},
        }
        created = (
            self.service.events()
            .insert(calendarId=self.calendar_id, body=event)
            .execute()
        )
        return {
            "event_id": created["id"],
            "start": start_dt.isoformat(),
            "html_link": created.get("htmlLink", ""),
        }

    def find_by_name(self, name: str, horizon_days: int = 60) -> list[dict]:
        """Findet kommende Termine deren Titel den Namen enthält (für Reschedule/Cancel-Flow)."""
        now = datetime.now(BERLIN)
        end = now + timedelta(days=horizon_days)
        events = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=20,
            )
            .execute()
        )
        needle = name.lower()
        return [
            {
                "event_id": e["id"],
                "summary": e.get("summary", ""),
                "start": e["start"].get("dateTime", ""),
            }
            for e in events.get("items", [])
            if needle in e.get("summary", "").lower()
        ]

    def reschedule(self, event_id: str, new_start_iso: str) -> dict:
        event = (
            self.service.events()
            .get(calendarId=self.calendar_id, eventId=event_id)
            .execute()
        )
        old_start = datetime.fromisoformat(event["start"]["dateTime"])
        old_end = datetime.fromisoformat(event["end"]["dateTime"])
        duration = old_end - old_start

        new_start = datetime.fromisoformat(new_start_iso)
        if new_start.tzinfo is None:
            new_start = new_start.replace(tzinfo=BERLIN)
        new_end = new_start + duration

        event["start"] = {"dateTime": new_start.isoformat(), "timeZone": "Europe/Berlin"}
        event["end"] = {"dateTime": new_end.isoformat(), "timeZone": "Europe/Berlin"}

        updated = (
            self.service.events()
            .update(calendarId=self.calendar_id, eventId=event_id, body=event)
            .execute()
        )
        return {"event_id": updated["id"], "start": new_start.isoformat()}

    def cancel(self, event_id: str) -> None:
        self.service.events().delete(
            calendarId=self.calendar_id, eventId=event_id
        ).execute()

    def _busy_ranges(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        events = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        ranges: list[tuple[datetime, datetime]] = []
        for e in events.get("items", []):
            s = e.get("start", {}).get("dateTime")
            t = e.get("end", {}).get("dateTime")
            if s and t:
                ranges.append((datetime.fromisoformat(s), datetime.fromisoformat(t)))
        return ranges
