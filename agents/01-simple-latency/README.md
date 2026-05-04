# Agent 01 — Simple Latency

Minimaler Voice-Agent, der das Grundprinzip einer LiveKit-Pipeline zeigt:

```
Mikrofon → Azure Speech (STT) → Gemini 2.5 Flash Lite via Vertex AI (LLM) → Azure Speech (TTS) → Lautsprecher
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
| LLM | Gemini 2.5 Flash Lite via Vertex AI | niedrige Latenz, EU-Region ohne Azure-OpenAI-Deployment |
| STT | Azure Speech (EU-Region) | gleicher Key und gleiche Resource wie TTS |
| TTS | Azure Speech Neural Voice | deutsche Stimmen, z. B. `de-DE-SeraphinaMultilingualNeural` |
| VAD | Silero (lokal) | läuft in-Process, keine API-Latenz |
| Turn Detection | LiveKit Multilingual | erkennt Gesprächsende besser als reine Silence-Detection |

## DSGVO-Status

- **Vertex AI:** EU-Region wie `europe-west4` setzen
- **Azure Speech:** Speech-Resource in EU-Region (`swedencentral`, `germanywestcentral`, `westeurope`) anlegen

Details → `docs/dsgvo-compliance.md`
