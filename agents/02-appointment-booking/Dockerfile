FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      gcc \
      ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY common/requirements-voice.txt /tmp/requirements-voice.txt
RUN pip install --no-cache-dir -r /tmp/requirements-voice.txt

COPY common/requirements-calendar.txt /tmp/requirements-calendar.txt
RUN pip install --no-cache-dir -r /tmp/requirements-calendar.txt

COPY 02-appointment-booking/pyproject.toml ./
COPY 02-appointment-booking/calendar_client.py 02-appointment-booking/agent.py ./

RUN python agent.py download-files || true

CMD ["python", "agent.py", "start"]
