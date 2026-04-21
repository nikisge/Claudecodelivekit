FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      gcc \
      ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY calendar_client.py agent.py ./

RUN python agent.py download-files || true

CMD ["python", "agent.py", "start"]
