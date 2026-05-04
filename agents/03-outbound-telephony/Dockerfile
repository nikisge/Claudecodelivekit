FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      gcc \
      ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY common/requirements-voice.txt /tmp/requirements-voice.txt
RUN pip install --no-cache-dir -r /tmp/requirements-voice.txt

COPY 03-outbound-telephony/pyproject.toml ./
COPY 03-outbound-telephony/prompts.py 03-outbound-telephony/agent.py ./

RUN python agent.py download-files || true

CMD ["python", "agent.py", "start"]
