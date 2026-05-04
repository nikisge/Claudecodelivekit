"""
Agent 01 — Simple Latency

Minimale STT → LLM → TTS-Pipeline. Zeigt das Grundprinzip eines LiveKit Voice-Agents
in möglichst wenig Code.

Provider (alle EU-Region / DSGVO-konform):
  STT: Azure Speech (EU-Region)
  LLM: Azure OpenAI GPT-4.1-mini (Sweden Central, EU Data Zone)
  TTS: Azure Speech Neural Voice (EU-Region)
  VAD: Silero (lokal, keine externe API)
  Turn Detection: LiveKit Multilingual Model (lokal)

Alternativen mit niedrigerer Latenz, aber mehr Provider-Setup:
  STT: Deepgram Nova-3 (EU-Endpoint)
  LLM: Google Gemini 2.5 Flash Lite via Vertex AI (europe-west4)
"""

import os
from dotenv import find_dotenv, load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import azure, openai, silero
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
