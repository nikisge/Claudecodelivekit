# Agent 01 — Simple Latency

Minimaler Voice-Agent, der das Grundprinzip einer LiveKit-Pipeline zeigt:

```
Mikrofon → Azure Speech (STT) → Azure OpenAI gpt-4.1-mini (LLM) → Azure Speech (TTS) → Lautsprecher
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
| LLM | Azure OpenAI gpt-4.1-mini (EU Data Zone) | gleicher Provider wie STT/TTS — Zuschauer braucht nur **eine** Cloud |
| STT | Azure Speech (EU-Region) | identische Resource wie TTS, nur ein Key |
| TTS | Azure Speech Neural Voice | deutsche Stimmen, z. B. `de-DE-SeraphinaMultilingualNeural` |
| VAD | Silero (lokal) | läuft in-Process, keine API-Latenz |
| Turn Detection | LiveKit Multilingual | erkennt Gesprächsende besser als reine Silence-Detection |

Wer experimentieren will, kann STT auf Deepgram (EU-Endpoint) und LLM auf Vertex AI Gemini 2.5 Flash Lite umstellen — das senkt die First-Response-Latenz, erfordert aber zusätzliche Provider-Keys. Die `.env` enthält die Variablen dafür weiterhin.

## DSGVO-Status

- **Azure OpenAI:** "EU Data Zone Standard"-Deployment in `swedencentral`, **nicht** "Global Standard"
- **Azure Speech:** Speech-Resource in EU-Region (`swedencentral`, `germanywestcentral`, `westeurope`) anlegen
- **Optional Vertex AI:** europe-west4, DPA via Google Cloud Terms
- **Optional Deepgram:** EU-Endpoint `https://api.eu.deepgram.com` nutzen, DPA/AVV abschließen, keine Trainingsnutzung vereinbaren

Details → `docs/dsgvo-compliance.md`
