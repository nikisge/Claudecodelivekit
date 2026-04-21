"""
Agent 02 — Appointment Booking

Buchungsassistent mit Tool-Calling gegen die echte Google Calendar API.
Demonstriert:
  • Function Calling in LiveKit (mehrere Tools, Multi-Turn-Flows)
  • Echte API-Integration statt Mock (Service-Account-Auth)
  • „Johanna"-Stimme von ElevenLabs für natürliches DE

Provider (alle DSGVO-konform):
  STT: Deepgram Nova-3 (EU)
  LLM: Azure OpenAI GPT-4.1-mini (Sweden Central, EU Data Zone)
  TTS: ElevenLabs Flash v2.5 „Johanna" (DE, enable_logging=False)
"""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import find_dotenv, load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, elevenlabs, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from calendar_client import CalendarClient

load_dotenv(find_dotenv(usecwd=True))

BERLIN = ZoneInfo("Europe/Berlin")


def _today_hint() -> str:
    now = datetime.now(BERLIN)
    return now.strftime("%A, %d.%m.%Y, %H:%M Uhr")


class AppointmentAgent(Agent):
    def __init__(self, calendar: CalendarClient) -> None:
        super().__init__(
            instructions=(
                "Du bist ein freundlicher Buchungsassistent für Termine. "
                "Du sprichst immer Deutsch, in kurzen und natürlichen Sätzen. "
                f"Heute ist {_today_hint()} (Zeitzone Europe/Berlin). "
                "Arbeitszeiten sind Montag bis Freitag, 9 bis 17 Uhr, in 30-Minuten-Slots. "
                "\n\n"
                "Ablauf:\n"
                "1. Frage nach dem Wunschtermin (Tag + ungefähre Uhrzeit).\n"
                "2. Nutze `list_free_slots`, um verfügbare Zeiten zu prüfen.\n"
                "3. Biete 1–2 konkrete Slots an, niemals eine lange Liste.\n"
                "4. Wenn der Nutzer zustimmt, frage nach dem Namen und buche mit `book_appointment`.\n"
                "5. Bestätige den gebuchten Termin mit Datum + Uhrzeit.\n"
                "\n"
                "Wenn der Nutzer einen Termin verschieben oder absagen möchte, "
                "nutze zuerst find_my_appointments mit dem Namen, "
                "danach reschedule_appointment oder cancel_appointment."
            ),
        )
        self._calendar = calendar

    @function_tool()
    async def list_free_slots(self, context: RunContext, date: str) -> str:
        """
        Gibt freie 30-Min-Slots an einem bestimmten Tag zurück.

        Args:
            date: Datum im Format YYYY-MM-DD (z. B. 2026-04-22).
        """
        slots = self._calendar.list_free_slots(date)
        if not slots:
            return f"Am {date} sind keine freien Termine verfügbar (oder Wochenende)."
        return "Freie Slots am " + date + ": " + ", ".join(
            datetime.fromisoformat(s).strftime("%H:%M") for s in slots
        )

    @function_tool()
    async def book_appointment(
        self,
        context: RunContext,
        start_iso: str,
        name: str,
        duration_min: int = 30,
        notes: str = "",
    ) -> str:
        """
        Bucht einen Termin.

        Args:
            start_iso: Startzeit im ISO-8601-Format (z. B. 2026-04-22T14:00:00+02:00).
            name: Name des Kunden, kommt in den Kalender-Titel.
            duration_min: Dauer in Minuten (Default 30).
            notes: Optionale Notiz für die Event-Beschreibung.
        """
        result = self._calendar.book(start_iso, duration_min, name, notes)
        return (
            f"Termin gebucht: {name}, "
            f"{datetime.fromisoformat(result['start']).strftime('%d.%m.%Y um %H:%M Uhr')}."
        )

    @function_tool()
    async def find_my_appointments(self, context: RunContext, name: str) -> str:
        """
        Findet kommende Termine eines Kunden anhand des Namens.

        Args:
            name: Name oder Namensteil, nach dem im Kalender-Titel gesucht wird.
        """
        hits = self._calendar.find_by_name(name)
        if not hits:
            return f"Keine kommenden Termine für {name} gefunden."
        lines = [
            f"- {datetime.fromisoformat(h['start']).strftime('%d.%m.%Y %H:%M')}: "
            f"{h['summary']} (ID: {h['event_id']})"
            for h in hits
        ]
        return "Gefundene Termine:\n" + "\n".join(lines)

    @function_tool()
    async def reschedule_appointment(
        self, context: RunContext, event_id: str, new_start_iso: str
    ) -> str:
        """
        Verschiebt einen bestehenden Termin.

        Args:
            event_id: Event-ID (vorher mit `find_my_appointments` holen).
            new_start_iso: Neue Startzeit im ISO-8601-Format.
        """
        result = self._calendar.reschedule(event_id, new_start_iso)
        return (
            f"Termin verschoben auf "
            f"{datetime.fromisoformat(result['start']).strftime('%d.%m.%Y %H:%M')} Uhr."
        )

    @function_tool()
    async def cancel_appointment(self, context: RunContext, event_id: str) -> str:
        """
        Sagt einen Termin ab.

        Args:
            event_id: Event-ID (vorher mit `find_my_appointments` holen).
        """
        self._calendar.cancel(event_id)
        return "Termin wurde abgesagt."


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    calendar = CalendarClient(
        service_account_path=os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "/secrets/gcp-sa.json"),
        calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
    )

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            base_url=os.getenv("DEEPGRAM_BASE_URL", "https://api.eu.deepgram.com"),
        ),
        llm=openai.LLM.with_azure(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        ),
        tts=elevenlabs.TTS(
            voice_id=os.getenv("ELEVEN_VOICE_ID"),
            model="eleven_flash_v2_5",
            language="de",
            enable_logging=False,
        ),
        turn_detection=MultilingualModel(),
    )

    await session.start(agent=AppointmentAgent(calendar), room=ctx.room)

    await session.generate_reply(
        instructions=(
            "Begrüße den Nutzer kurz auf Deutsch und frage, ob er einen neuen Termin buchen "
            "oder einen bestehenden ändern möchte."
        ),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="appointment-booking",
        )
    )
