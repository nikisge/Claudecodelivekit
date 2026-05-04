FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      gcc \
      ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY common/requirements-simple.txt /tmp/requirements-simple.txt
RUN pip install --no-cache-dir -r /tmp/requirements-simple.txt

COPY 01-simple-latency/pyproject.toml ./
COPY 01-simple-latency/agent.py ./

# LiveKit VAD/Turn-Detector laden Modell-Gewichte beim ersten Start;
# Pre-Download spart Zeit beim Cold-Start im Prod.
RUN python agent.py download-files || true

CMD ["python", "agent.py", "start"]
