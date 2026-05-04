#!/usr/bin/env bash
# One-Shot-Installer für einen frischen VPS (Ubuntu/Debian).
# Installiert Docker + Compose-Plugin, öffnet die nötigen Firewall-Regeln,
# generiert LiveKit-Keys und erstellt das secrets/-Verzeichnis.
#
# Nutzung auf einem leeren Server:
#   git clone https://github.com/nikisge/Claudecodelivekit.git
#   cd Claudecodelivekit
#   sudo ./scripts/install-vps.sh
#
# Danach nur noch:
#   1. .env mit GOOGLE_CLOUD_PROJECT + AZURE_SPEECH_KEY füllen
#   2. Service-Account-JSON nach secrets/gcp-sa.json legen
#   3. ./start.sh setup   (baut Agent-Images, ~5 Min)
#   4. ./start.sh         (startet Infrastruktur)

set -euo pipefail

cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}→${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err() { echo -e "${RED}✗${NC} $*"; }

if [[ $EUID -ne 0 ]]; then
  err "Bitte als root oder mit sudo ausführen: sudo ./scripts/install-vps.sh"
  exit 1
fi

# ── 1. Docker installieren (idempotent) ───────────────────────────────────────
if command -v docker >/dev/null 2>&1; then
  log "Docker ist bereits installiert: $(docker --version)"
else
  log "Installiere Docker (über get.docker.com)..."
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sh /tmp/get-docker.sh
  rm /tmp/get-docker.sh
fi

if docker compose version >/dev/null 2>&1; then
  log "Docker Compose Plugin ist bereits installiert: $(docker compose version --short)"
else
  log "Installiere Docker Compose Plugin..."
  apt-get update -qq
  apt-get install -y -qq docker-compose-plugin
fi

# ── 2. Firewall-Regeln (UFW, Regeln nur hinzufügen, nicht aktivieren) ────────
if command -v ufw >/dev/null 2>&1; then
  log "Setze UFW-Regeln (UFW wird NICHT automatisch aktiviert)..."
  ufw allow ssh                       >/dev/null
  ufw allow 80/tcp                    >/dev/null
  ufw allow 443/tcp                   >/dev/null
  ufw allow 7881/tcp                  >/dev/null
  ufw allow 50000:50060/udp           >/dev/null
  ufw allow 5060/udp                  >/dev/null
  ufw allow 5060/tcp                  >/dev/null
  ufw allow 10000:20000/udp           >/dev/null
  log "UFW-Regeln gesetzt. Aktiviere bei Bedarf manuell mit: ufw enable"
else
  warn "UFW nicht installiert — Firewall-Regeln übersprungen."
fi

# ── 3. .env aus .env.example + LiveKit-Keys generieren ───────────────────────
if [[ -f .env ]]; then
  log ".env existiert bereits — überspringe."
else
  log "Erstelle .env aus .env.example..."
  cp .env.example .env

  log "Generiere LiveKit API-Key + Secret..."
  API_KEY="APIk$(openssl rand -hex 6)"
  API_SECRET="$(openssl rand -hex 32)"
  sed -i "s|^LIVEKIT_API_KEY=.*|LIVEKIT_API_KEY=${API_KEY}|" .env
  sed -i "s|^LIVEKIT_API_SECRET=.*|LIVEKIT_API_SECRET=${API_SECRET}|" .env
fi

# ── 4. secrets/-Verzeichnis ──────────────────────────────────────────────────
mkdir -p secrets
log "secrets/-Verzeichnis bereit unter $(pwd)/secrets/"

# ── 5. Status + nächste Schritte ─────────────────────────────────────────────
echo
echo "════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Server-Vorbereitung abgeschlossen.${NC}"
echo "════════════════════════════════════════════════════════════════════════"
echo
echo "Nächste Schritte (nur noch 4 Sachen):"
echo
echo "  1. ${YELLOW}.env editieren${NC} — folgende Werte setzen:"
echo "       GOOGLE_CLOUD_PROJECT=<deine-gcp-project-id>"
echo "       AZURE_SPEECH_KEY=<dein-azure-speech-key>"
echo "       APP_DOMAIN=<deine-domain-oder-sslip-pseudo-domain>"
echo "       LIVEKIT_DOMAIN=<lk.deine-domain>"
echo "       CADDY_EMAIL=<deine-email-für-letsencrypt>"
echo "       LIVEKIT_URL=wss://<deine-livekit-domain>"
echo
echo "  2. ${YELLOW}Google-Service-Account-JSON hochladen${NC}:"
echo "       scp gcp-sa.json root@<vps-ip>:$(pwd)/secrets/gcp-sa.json"
echo
echo "  3. ${YELLOW}Agent-Images bauen${NC} (einmalig, ~5 Min):"
echo "       ./start.sh setup"
echo
echo "  4. ${YELLOW}Alles starten${NC}:"
echo "       docker compose up -d --build       # Produktion mit TLS"
echo "       ODER  ./start.sh                   # nur Infra für lokales Testen"
echo
echo "Provider-Setup-Details: docs/credentials-setup.md"
echo "════════════════════════════════════════════════════════════════════════"
