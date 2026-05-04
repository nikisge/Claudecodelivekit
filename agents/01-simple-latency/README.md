# Agent 01 — Simple Latency (Native Audio)

Voice-Agent mit Speech-to-Speech-Modell. Audio geht direkt ins Modell rein und kommt direkt wieder raus — kein STT/TTS dazwischen:

```
Mikrofon → Gemini 2.5 Flash Native Audio (Vertex AI, europe-west4) → Lautsprecher
                                    │
                                    └── VAD + Turn-Detection im Modell selbst
```

## Lokal starten

1. Aus dem Repo-Root `./scripts/generate-keys.sh` und `.env` mit Provider-Keys füllen (nur GCP nötig — siehe unten).
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

## Warum diese Konfiguration?

| Komponente | Gewählt | Grund |
|---|---|---|
| Realtime LLM | `gemini-live-2.5-flash-native-audio` via Vertex AI | Speech-to-Speech in einem Hop, niedrigste Latenz, GA-Modell mit EU-Region-Support |
| Voice | `Aoede` (oder `Puck`, `Charon`, `Kore`, `Fenrir`) | Native multilingual — sprechen Deutsch ohne US-Akzent. Override via `GEMINI_LIVE_VOICE` |
| Region | `europe-west4` (Niederlande) | Inferenz garantiert in der EU, DSGVO-konform |
| VAD / Turn-Detection | im Modell | keine separaten Plugins (Silero, Multilingual) nötig |

## DSGVO-Status

- **Vertex AI Live API GA:** das Modell `gemini-live-2.5-flash-native-audio` ist in `europe-west4` und 5 weiteren EU-Regionen deployt. ML-Inferenz garantiert in der gewählten Region.
- **Nicht** das Preview-Modell `gemini-2.5-flash-native-audio-preview-...` nutzen — US-only und wird abgeschaltet.

Details → `docs/dsgvo-compliance.md`

## Caveats

- **Session-Limit 10 Min** (per Default, verlängerbar). Für lange Gespräche ist die klassische STT→LLM→TTS-Pipeline aus Agent 02 die robustere Wahl.
- **Pricing**: Audio wird mit ~25 Tokens/Sekunde abgerechnet (Input $3/1M, Output $12/1M). Pro Turn werden alle Tokens des Session-Context-Windows neu berechnet — lange Konversationen werden überproportional teuer.
- **Tool Calling** ist auf der GA-Version supported, war aber auf älteren Preview-Varianten teils kaputt. Agent 02/03 (mit Tools) bleiben deshalb bewusst auf der klassischen Pipeline.
