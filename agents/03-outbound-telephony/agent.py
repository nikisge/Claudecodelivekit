"""
Agent 03 — Outbound Lead Qualifier

Wartet auf Dispatches vom Frontend-Formular, bekommt Name + Telefonnummer + Kontext
als JSON-Metadata, qualifiziert den Lead in ~3 Min und pusht das Ergebnis per
Data-Channel zurück an das Frontend (wo der Absender live sieht, was passiert).

Provider (DSGVO-konform):
  STT: Azure Speech (EU-Region)
  LLM: Azure OpenAI GPT-4.1-mini (Sweden Central)
  TTS: Azure Speech Neural Voice (EU-Region)

Voraussetzung: LIVEKIT_OUTBOUND_TRUNK_ID ist gesetzt (über scripts/setup-sip.py einmalig erzeugt).
"""

from __future__ import annotations

import json
import os

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
from livekit.plugins import azure, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompts import LEAD_QUALIFIER_SYSTEM_PROMPT

load_dotenv(find_dotenv(usecwd=True))


class LeadQualifierAgent(Agent):
    def __init__(self, caller_name: str, context_info: str) -> None:
        super().__init__(
            instructions=LEAD_QUALIFIER_SYSTEM_PROMPT.format(
                name=caller_name,
                context=context_info,
            )
        )

    @function_tool()
    async def save_lead(
        self,
        context: RunContext,
        budget_eur: str,
        timeline: str,
        use_case: str,
        interest_level: str,
        is_decision_maker: bool,
        notes: str = "",
    ) -> str:
        """
        Speichert die Lead-Qualifikation am Gesprächsende und broadcastet sie ans Frontend.

        Args:
            budget_eur: grober Budget-Rahmen, z.B. "unter 5k", "5-20k", "20k+".
            timeline: Zeitplan des Interessenten, z.B. "sofort", "Q3 2026".
            use_case: kurze Beschreibung des Anliegens.
            interest_level: "hoch", "mittel" oder "niedrig".
            is_decision_maker: True wenn der Kontakt alleine entscheiden kann.
            notes: freie Notizen.
        """
        lead = {
            "budget_eur": budget_eur,
            "timeline": timeline,
            "use_case": use_case,
            "interest_level": interest_level,
            "is_decision_maker": is_decision_maker,
            "notes": notes,
        }
        payload = json.dumps({"type": "lead_qualified", "data": lead}).encode()
        await context.room.local_participant.publish_data(payload=payload, reliable=True)
        return "Lead gespeichert."

    @function_tool()
    async def end_call(self, context: RunContext) -> str:
        """Beendet das Gespräch nach dem Speichern des Leads."""
        await context.room.disconnect()
        return "Gespräch beendet."


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    metadata = {}
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
        except json.JSONDecodeError:
            pass

    caller_name = metadata.get("name", "Interessent")
    context_info = metadata.get("context", "Allgemeines Interesse")

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=azure.STT(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION", "swedencentral"),
            language=os.getenv("AZURE_SPEECH_LANGUAGE", "de-DE"),
        ),
        llm=openai.LLM.with_azure(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        ),
        tts=azure.TTS(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION", "swedencentral"),
            voice=os.getenv("AZURE_SPEECH_VOICE", "de-DE-SeraphinaMultilingualNeural"),
            language=os.getenv("AZURE_SPEECH_LANGUAGE", "de-DE"),
        ),
        turn_detection=MultilingualModel(),
    )

    await session.start(agent=LeadQualifierAgent(caller_name, context_info), room=ctx.room)

    # Bei Outbound-Calls wartet das LiveKit-SIP-Service bis der Angerufene abhebt,
    # dann tritt der SIP-Teilnehmer dem Room bei und der Agent beginnt.
    await session.generate_reply(
        instructions=(
            f"Begrüße {caller_name} kurz auf Deutsch. Stelle dich als KI-Assistentin vor, "
            "die wegen der Formular-Anfrage anruft, und frage ob der Moment gerade passt."
        ),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-telephony",
        )
    )
