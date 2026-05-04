"""
Agent 01 — Simple Latency

Minimale STT → LLM → TTS-Pipeline. Zeigt das Grundprinzip eines LiveKit Voice-Agents
in möglichst wenig Code.

Provider (alle EU-Region / DSGVO-konform):
  STT: Azure Speech (EU-Region)
  LLM: Google Gemini 2.5 Flash Lite via Vertex AI (EU-Region)
  TTS: Azure Speech Neural Voice (EU-Region)
  VAD: Silero (lokal, keine externe API)
  Turn Detection: LiveKit Multilingual Model (lokal)
"""

import os
from dotenv import find_dotenv, load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import azure, google, silero
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
        stt=azure.STT(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION", "swedencentral"),
            language=os.getenv("AZURE_SPEECH_LANGUAGE", "de-DE"),
        ),
        llm=google.LLM(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west4"),
        ),
        tts=azure.TTS(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION", "swedencentral"),
            voice=os.getenv("AZURE_SPEECH_VOICE", "de-DE-SeraphinaMultilingualNeural"),
            language=os.getenv("AZURE_SPEECH_LANGUAGE", "de-DE"),
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
