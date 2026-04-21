FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      gcc \
      ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY agent.py ./

# LiveKit VAD/Turn-Detector laden Modell-Gewichte beim ersten Start;
# Pre-Download spart Zeit beim Cold-Start im Prod.
RUN python agent.py download-files || true

CMD ["python", "agent.py", "start"]
