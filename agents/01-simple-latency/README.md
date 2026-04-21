# Agent 01 — Simple Latency

Minimaler Voice-Agent, der das Grundprinzip einer LiveKit-Pipeline zeigt:

```
Mikrofon → Deepgram (STT) → Gemini 2.5 Flash Lite (LLM) → Cartesia (TTS) → Lautsprecher
                                    │
                                    └── Silero VAD + Multilingual Turn Detection
```

## Lokal starten

1. Aus dem Repo-Root `./scripts/generate-keys.sh` und `.env` mit Provider-Keys füllen.
2. LiveKit-Server starten:
   ```bash
   docker compose -f docker-compose.local.yml up -d redis livekit-server
   ```
3. Agent im Dev-Mode (Hot-Reload) starten:
   ```bash
   cd agents/01-simple-latency
   uv sync    # oder: python -m venv .venv && .venv/bin/pip install .
   uv run python agent.py dev
   ```
4. Frontend in separatem Terminal starten → Browser auf `http://localhost:3000`.

## Warum diese Provider?

| Komponente | Gewählt | Grund |
|---|---|---|
| LLM | Gemini 2.5 Flash Lite (Vertex EU) | niedrigste First-Token-Latenz unter DSGVO-konformen Optionen |
| STT | Deepgram Nova-3 (EU-Endpoint `api.eu.deepgram.com`) | schnellstes Streaming-STT mit guter DE-Erkennung |
| TTS | Cartesia Sonic Multilingual | ~100ms First-Audio-Latenz, deutsche Stimmen verfügbar |
| VAD | Silero (lokal) | läuft in-Process, keine API-Latenz |
| Turn Detection | LiveKit Multilingual | erkennt Gesprächsende besser als reine Silence-Detection |

## DSGVO-Status

- **Vertex AI:** europe-west4, DPA via Google Cloud Terms
- **Deepgram EU:** Frankfurt-Region, SCCs
- **Cartesia:** Zero-Retention-Mode in der Cartesia-Konsole aktivieren (`Data Retention: None`), DPA anfordern

Details → `docs/dsgvo-compliance.md`
