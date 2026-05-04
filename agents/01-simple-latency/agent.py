"""
Agent 01 — Simple Latency

Minimale STT → LLM → TTS-Pipeline. Zeigt das Grundprinzip eines LiveKit Voice-Agents
in möglichst wenig Code, optimiert auf First-Response-Latenz.

Provider (alle EU-Region / DSGVO-konform):
  STT: Deepgram Nova-3 (EU-Endpoint)
  LLM: Google Gemini 2.5 Flash Lite via Vertex AI (europe-west4)
  TTS: Cartesia Sonic Multilingual (deutsche Stimme, Zero-Retention)
  VAD: Silero (lokal, keine externe API)
  Turn Detection: LiveKit Multilingual Model (lokal)
"""

import os
from dotenv import find_dotenv, load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import cartesia, deepgram, google, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(find_dotenv(usecwd=True))


class SimpleLatencyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "Du bist ein freundlicher, hilfsbereiter Voice-Assistent. "
                "Antworte immer auf Deutsch, in kurzen und natürlichen Sätzen. "
                "Du bist Teil eines Tutorial-Videos über LiveKit — wenn jemand fragt was du bist, "
                "erkläre kurz, dass du ein Demo-Agent bist, der die STT→LLM→TTS-Pipeline zeigt."
            ),
        )


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-3",
            language="de",
            base_url=os.getenv("DEEPGRAM_BASE_URL", "https://api.eu.deepgram.com"),
        ),
        llm=google.LLM(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west4"),
        ),
        tts=cartesia.TTS(
            model="sonic-multilingual",
            voice=os.getenv("CARTESIA_VOICE_ID"),
            language="de",
        ),
        turn_detection=MultilingualModel(),
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
