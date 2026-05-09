# VPS-Deployment (Hostinger o. ä.)

Ziel: alle 3 Agents + Frontend + LiveKit-Server hinter TLS auf deinem VPS laufen lassen. Agent 3 (Outbound-Call) funktioniert erst auf dem VPS, weil Twilio eine öffentlich erreichbare SIP-Adresse braucht.

## Voraussetzungen

- VPS mit min. 2 vCPU / 4 GB RAM (z. B. Hostinger KVM 2 oder Hetzner CX22) — Ubuntu 22.04+
- Eine Domain (z. B. `voice.meine-domain.de` + Subdomain `lk.meine-domain.de`)
- Twilio-Account mit einer SIP-trunkfähigen Nummer

## 1. DNS setzen (vor dem VPS-Setup)

A-Records setzen, beide auf die VPS-IP:

```
voice.meine-domain.de      A    <vps-ip>
lk.meine-domain.de         A    <vps-ip>
```

**Wichtig:** Cloudflare-Proxy **aus** (grauen Pfeil). Der Proxy bricht WebSockets + UDP.

## 2. VPS aufsetzen

Als root einloggen:

```bash
# Docker + Compose
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin git

# Firewall (UFW)
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

## 3. Repo clonen und `.env` füllen

```bash
cd /opt
git clone https://github.com/nikisge/Claudecodelivekit.git
cd Claudecodelivekit
./scripts/generate-keys.sh
nano .env
```

In `.env`:
```bash
APP_DOMAIN=voice.meine-domain.de
LIVEKIT_DOMAIN=lk.meine-domain.de
CADDY_EMAIL=admin@meine-domain.de
LIVEKIT_URL=wss://lk.meine-domain.de
# + alle Provider-Keys (siehe docs/dsgvo-compliance.md)
```

## 4. Google-Service-Account-JSON auf VPS kopieren

Vom Mac aus:
```bash
scp ~/Downloads/gcp-sa.json root@<vps-ip>:/opt/Claudecodelivekit/secrets/
```

In `.env`:
```
GOOGLE_SERVICE_ACCOUNT_PATH=./secrets/gcp-sa.json
```

## 5. Alles hochfahren

```bash
docker compose up -d --build
docker compose ps   # alle Services sollten "Up" sein
docker compose logs -f caddy   # TLS-Erhalt beobachten
```

Caddy holt automatisch Let's-Encrypt-Zertifikate für beide Domains. Öffne
`https://voice.meine-domain.de` → Landing-Page erscheint.

## 6. Twilio SIP Trunk → LiveKit verbinden

Siehe `docs/twilio-setup.md`. Kurz:

1. Twilio Console → Elastic SIP Trunking → neuer Trunk
2. Origination URI: `sip:<vps-ip>:5060;transport=udp`
3. Dein Twilio-Kauf-Nummer dem Trunk zuweisen
4. Trunk-Zugangsdaten (SID, Token) + Trunk-URI in VPS `.env` eintragen
5. Auf VPS: `python3 -m pip install livekit python-dotenv` und danach `python3 scripts/setup-sip.py`
6. Die ausgegebene `LIVEKIT_OUTBOUND_TRUNK_ID` in `.env` setzen
7. `docker compose up -d --force-recreate frontend` (damit die Variable in Next.js Runtime ankommt)

## 7. Smoke-Tests auf VPS

| Test | So |
|---|---|
| Landing-Page | `https://voice.meine-domain.de` — drei Kacheln sichtbar |
| Agent 1 | Klicke „Simple Latency" → Audio erlauben → Gespräch starten → Begrüßung hörbar |
| Agent 2 | Klicke „Termin-Assistent" → „Freitag 14 Uhr buchen, ich bin Max" → Termin erscheint im Google Kalender |
| Agent 3 | Klicke „Outbound-Anruf" → Formular ausfüllen mit echter Handynr. → Handy klingelt |

## Logs

```bash
docker compose logs -f agent-simple-latency
docker compose logs -f agent-appointment-booking
docker compose logs -f agent-outbound-telephony
docker compose logs -f livekit-server
docker compose logs -f livekit-sip
```

## Production-Hardening (nicht im Tutorial-Scope)

Für echten Produktivbetrieb würdest du noch ergänzen:
- Auth-Layer vor `/api/token` und `/api/dispatch-call` (JWT, Session-Cookies)
- Rate-Limiting (z. B. per Cloudflare WAF oder Caddy plugin)
- Monitoring (Prometheus + Grafana, LiveKit expose Metrics auf Port 6789)
- Automatische Backups vom Redis-State (optional — LiveKit State ist transient)
- Watchtower für Docker-Image-Updates
