"""
Agent 01 — Simple Latency (Native Audio)

Speech-to-Speech-Pipeline mit Gemini Live API: Audio direkt rein, Audio direkt
raus. Kein separates STT/TTS — niedrigere Latenz und natürlicheres Turn-Taking
als die klassische STT→LLM→TTS-Pipeline.

Provider (DSGVO-konform):
  Realtime LLM: Gemini 2.5 Flash Native Audio via Vertex AI (europe-west4)

VAD und Turn-Detection übernimmt das Live-Modell selbst — kein Silero-Plugin.
"""

import os
from dotenv import find_dotenv, load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import google

load_dotenv(find_dotenv(usecwd=True))


class SimpleLatencyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "Du bist ein freundlicher, hilfsbereiter Voice-Assistent. "
                "Antworte immer auf Deutsch, in kurzen und natürlichen Sätzen. "
                "Du bist Teil eines Tutorial-Videos über LiveKit — wenn jemand fragt was du bist, "
                "erkläre kurz, dass du ein Demo-Agent bist, der die Speech-to-Speech-Pipeline "
                "mit der Gemini Live API zeigt."
            ),
        )


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model=os.getenv("GEMINI_LIVE_MODEL", "gemini-live-2.5-flash-native-audio"),
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west4"),
            voice=os.getenv("GEMINI_LIVE_VOICE", "Aoede"),
            language=os.getenv("GEMINI_LIVE_LANGUAGE", "de-DE"),
        ),
    )

    await session.start(agent=SimpleLatencyAgent(), room=ctx.room)

    await session.generate_reply(
        instructions="Begrüße den Nutzer kurz auf Deutsch und frage, wie du helfen kannst.",
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="simple-latency",
        )
    )
