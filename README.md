# LiveKit Voice Agents - DSGVO-konform, selbst gehostet

Begleit-Repo zum YouTube-Tutorial. Das Projekt zeigt drei deutsche Voice-AI-Agents mit [LiveKit](https://livekit.io), selbst gehostetem LiveKit-Server, Next.js-Frontend und optionaler Twilio-SIP-Telefonie auf einem VPS.

## Projekt in Kurzform

| # | Agent | Zweck |
|---|---|---|
| **01** | `simple-latency` | Speech-to-Speech mit Gemini 2.5 Flash Live API (Vertex AI, EU). Kein STT/TTS-Hop — Audio direkt rein und raus. |
| **02** | `appointment-booking` | Terminassistent mit Tool Calling gegen Google Calendar. Kann freie Slots prüfen, Termine buchen, verschieben und absagen. |
| **03** | `outbound-telephony` | Outbound-Lead-Qualifier. Das Frontend startet einen Anruf, LiveKit-SIP ruft via Twilio an, der Agent qualifiziert den Lead und sendet JSON zurück. |

Die lokale Docker-Variante startet nur die Infrastruktur dauerhaft. Agent-Container werden im Browser pro Kachel gestartet und gestoppt. Auf dem VPS laufen alle Services dauerhaft per Docker Compose.

## VPS Quick-Setup (1 Befehl)

Auf einem **leeren Ubuntu/Debian-VPS** (ohne Docker etc.) reicht ein Befehl, um alles zu installieren:

```bash
git clone https://github.com/nikisge/Claudecodelivekit.git
cd Claudecodelivekit
sudo ./scripts/install-vps.sh
```

Das installiert Docker + Compose-Plugin, setzt die Firewall-Regeln, erzeugt die LiveKit-Keys und legt `secrets/` an. Danach nur noch:

1. **`.env` editieren** und mindestens diese Werte setzen:
   - `GOOGLE_CLOUD_PROJECT` (Vertex AI Project-ID)
   - `AZURE_SPEECH_KEY` (Azure Speech Resource Key)
   - `APP_DOMAIN`, `LIVEKIT_DOMAIN`, `CADDY_EMAIL`, `LIVEKIT_URL` (für TLS-Produktion)
2. **Service-Account-JSON nach `secrets/gcp-sa.json` legen**
3. **Services bauen + starten**:
   ```bash
   ./start.sh vps 1            # nutzt automatisch sslip.io + Caddy TLS
   ```

Provider-Setup-Details siehe `docs/credentials-setup.md`.

## Lokal starten

Voraussetzungen: Docker Desktop, ein gefülltes `.env`, Provider-Keys und für Agent 1/2 die Google-Service-Account-Datei unter `./secrets/gcp-sa.json`.

```bash
git clone https://github.com/nikisge/Claudecodelivekit.git
cd Claudecodelivekit

./scripts/generate-keys.sh
# Danach .env öffnen und Provider-Keys eintragen:
# Azure Speech, Google Cloud/Vertex, Google Calendar

./start.sh setup
./start.sh
```

Dann im Browser öffnen:

```text
http://localhost:3000
```

Was die Befehle machen:

| Befehl | Effekt |
|---|---|
| `./start.sh setup` | Baut nur die lokale Infrastruktur, vor allem das Frontend. Schnellster Demo-Start nach Clone. |
| `./start.sh setup 1` | Baut nur Agent 1 und legt `voice-agent-1` an, startet ihn aber noch nicht. |
| `./start.sh setup 2` | Baut nur Agent 2 und legt `voice-agent-2` an, startet ihn aber noch nicht. |
| `./start.sh setup 3` | Baut nur Agent 3 und legt `voice-agent-3` an, startet ihn aber noch nicht. |
| `./start.sh setup all` | Baut alle drei Agent-Images. Nur nutzen, wenn du wirklich alle drei in derselben Demo brauchst. |
| `./start.sh` oder `./start.sh up` | Startet Redis, LiveKit und das Frontend. Danach steuerst du die Agents im Browser. |
| `./start.sh status` | Zeigt Infrastruktur und Agent-Container. |
| `./start.sh logs` | Zeigt laufende Logs aller lokalen Compose-Services. |
| `./start.sh agent-logs 1` | Zeigt Logs von Agent 1. Für Agent 2/3 entsprechend `2` oder `3`. |
| `./start.sh stop` | Stoppt Infrastruktur und eventuell laufende Agents. |

Wenn im Browser bei einer Agent-Kachel `missing` oder ein Container-Fehler erscheint, wurde der konkrete Agent noch nicht vorbereitet. Nutze dann `./start.sh setup 1`, `./start.sh setup 2` oder `./start.sh setup 3`.

Hinweis zu Build-Zeit und Image-Größe: Agent 2 und 3 nutzen Silero VAD + Multilingual Turn Detection. Die Dockerfiles installieren dafür CPU-only PyTorch, damit keine CUDA/GPU-Pakete mitgebaut werden. Der erste Build dauert trotzdem deutlich länger als Agent 1.

Latenz-Tipp für Agent 2/3: Gemini 2.5 Flash läuft mit deaktiviertem Thinking. Für Azure Speech nimm eine Speech-Region nahe am Server und normale Neural Voices wie `de-DE-SeraphinaMultilingualNeural` oder `de-DE-FlorianMultilingualNeural`; die `DragonHD...`-Voices sind eher Qualitäts- als Demo-Latenz-Optimierung.

### Lokal entwickeln

Für normales Testen reicht Docker. Wenn du an einem Agent arbeitest und Hot Reload willst, kannst du den jeweiligen Agent außerhalb von Docker starten:

```bash
cd agents/01-simple-latency
uv sync
uv run python agent.py dev
```

Dafür muss die Infrastruktur trotzdem laufen:

```bash
./start.sh
```

## Lokal stoppen

```bash
./start.sh stop
```

Das fährt auch Agent-Container runter, die du vorher im Browser gestartet hast. Falls du nur einzelne Agents stoppen willst, nutze die Stop-Buttons in der UI.

## VPS starten

Ziel: `https://voice.deine-domain.de` fürs Frontend und `wss://lk.deine-domain.de` für LiveKit. Agent 3 braucht den VPS, weil Twilio eine öffentlich erreichbare SIP-Adresse benötigt.

1. DNS setzen:

```text
voice.deine-domain.de  A  <vps-ip>
lk.deine-domain.de     A  <vps-ip>
```

Cloudflare-Proxy dabei ausschalten, falls du Cloudflare nutzt.

2. Docker, Compose und Firewall auf dem VPS installieren:

```bash
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin git

ufw default deny incoming
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 7881/tcp
ufw allow 50000:50060/udp
ufw allow 5060/udp
ufw allow 5060/tcp
ufw allow 10000:20000/udp
ufw enable
```

3. Projekt deployen und `.env` füllen:

```bash
cd /opt
git clone https://github.com/nikisge/Claudecodelivekit.git
cd Claudecodelivekit
./scripts/generate-keys.sh
nano .env
```

Wichtige VPS-Werte, wenn du eine eigene Domain nutzt:

```bash
APP_DOMAIN=voice.deine-domain.de
LIVEKIT_DOMAIN=lk.deine-domain.de
CADDY_EMAIL=admin@deine-domain.de
LIVEKIT_URL=wss://lk.deine-domain.de
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
```

Ohne eigene Domain setzt `./start.sh vps 1` automatisch kostenlose sslip.io-Domains anhand der Server-IP, z. B.:

```bash
APP_DOMAIN=voice-187-124-175-89.sslip.io
LIVEKIT_DOMAIN=lk-187-124-175-89.sslip.io
LIVEKIT_URL=wss://lk-187-124-175-89.sslip.io
```

4. Google-Service-Account-Datei auf den VPS legen:

```bash
mkdir -p secrets
# Vom lokalen Rechner:
scp ~/Downloads/gcp-sa.json root@<vps-ip>:/opt/Claudecodelivekit/secrets/gcp-sa.json
```

5. Infrastruktur und den gewünschten Agent starten:

```bash
./start.sh vps 1
```

Caddy holt automatisch TLS-Zertifikate. Danach ist das Frontend über die ausgegebene HTTPS-URL erreichbar.

Weitere Agents schaltest du nur bei Bedarf dazu:

```bash
./start.sh vps 2
./start.sh vps 3
./start.sh vps all
```

Einzelne Agents stoppst du entweder im Frontend über den Stop-Button oder per CLI:

```bash
./start.sh vps-stop 1
./start.sh vps-stop 2
./start.sh vps-stop 3
./start.sh vps-stop all
```

VPS stoppen:

```bash
docker compose down
```

Nach `.env`-Änderungen:

```bash
docker compose up -d --force-recreate
```

## Twilio SIP einrichten

Agent 3 braucht zusätzlich einen Twilio Elastic SIP Trunk.

1. In Twilio eine Voice-fähige Telefonnummer kaufen.
2. Elastic SIP Trunk anlegen.
3. Unter **Termination** die Twilio-Trunk-Domain notieren, z. B. `voiceagents.pstn.twilio.com`.
4. Unter **Authentication** eine Credential List anlegen. Diese Werte in `.env` eintragen, nicht den normalen Twilio Account-Auth-Token:

```bash
TWILIO_SIP_TRUNK_URI=sip:voiceagents.pstn.twilio.com
TWILIO_ACCOUNT_SID=<trunk-credential-username>
TWILIO_AUTH_TOKEN=<trunk-credential-password>
TWILIO_PHONE_NUMBER=+491701234567
```

5. LiveKit-Outbound-Trunk erzeugen:

```bash
cd /opt/Claudecodelivekit
python3 -m pip install livekit python-dotenv
python3 scripts/setup-sip.py
```

6. Die ausgegebene ID in `.env` eintragen:

```bash
LIVEKIT_OUTBOUND_TRUNK_ID=ST_...
```

7. Frontend neu starten, damit die Dispatch-Route die neue Variable sieht:

```bash
docker compose up -d --force-recreate frontend
```

Danach `https://voice.deine-domain.de/outbound` öffnen, Name und E.164-Telefonnummer eintragen, z. B. `+491701234567`.

Details: `docs/twilio-setup.md` und `docs/vps-deployment.md`.

## Architektur

```
Internet ──┬─▶ Caddy (Auto-TLS) ──┬─▶ Frontend (Next.js)
           │                      └─▶ LiveKit-Server (WebSocket)
           └─▶ Twilio SIP Trunk ──────▶ LiveKit-SIP ──▶ LiveKit-Server
                                                           │
                                                           ├─▶ Agent 1 (Python)
                                                           ├─▶ Agent 2 (Python)
                                                           └─▶ Agent 3 (Python)
```

Alle Agents verbinden sich als LiveKit-Worker zum Server und warten auf Dispatch.

## DSGVO-Konformität

Das Repo ist auf EU-Regionen und Zero-Retention-Optionen ausgelegt. Prüfe trotzdem pro Provider aktiv die Einstellungen und DPAs:

- Azure Speech-Resource in EU-Region anlegen.
- Google Cloud Region `europe-west4` oder passend EU wählen.
- Deepgram (optional als STT-Alternative) nur mit EU-Endpoint und DPA/AVV nutzen.
- Twilio DPA unterzeichnen und passende Region nutzen.

Mehr Details stehen in `docs/dsgvo-compliance.md`.

## Projekt-Struktur

```
Claudecodelivekit/
├── docker-compose.yml          # VPS-Produktion
├── docker-compose.local.yml    # Lokales Docker-Setup
├── Caddyfile                   # TLS-Reverse-Proxy
├── livekit.yaml                # LiveKit-Config für VPS
├── livekit.local.yaml          # LiveKit-Config für lokal
├── .env.example                # Env-Template mit DSGVO-Kommentaren
│
├── agents/                     # Drei Voice-Agents in Python
├── frontend/                   # Next.js-UI (Browser-Test + Outbound-Formular)
├── scripts/                    # Setup-Helfer (Keys, SIP)
└── docs/                       # Deutschsprachige Setup-Guides
```

## Weitere Doku

- `docs/credentials-setup.md` - Provider-Keys und Service Accounts
- `docs/quickstart-lokal.md` - lokale Entwicklung im Detail
- `docs/vps-deployment.md` - VPS-Schritte ausführlicher
- `docs/twilio-setup.md` - Twilio Elastic SIP Trunk
- `docs/google-calendar-setup.md` - Google Calendar Integration

## Lizenz

MIT
