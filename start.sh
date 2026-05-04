#!/usr/bin/env bash
# One-Command-Workflow für Zuschauer.
#
# Typischer Ablauf:
#   ./start.sh setup   → einmalig: Infrastruktur bauen
#   ./start.sh setup 1 → nur Agent 1 vorbereiten (2/3/all analog)
#   ./start.sh         → Infrastructure starten, Agents kontrolliert man im Browser
#   ./start.sh stop    → alles stoppen
#
# Im Browser (http://localhost:3000):
#   - jede Agent-Kachel hat eigenen Start/Stop-Button
#   - Erster Start eines Agents: ~5–15 Sek (Model-Load)
#   - Weiterer Start: sofort

set -euo pipefail

cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.local.yml"
PROD_COMPOSE="docker compose"

agent_service() {
  case "$1" in
    1|simple|simple-latency) echo "agent-simple-latency" ;;
    2|appointment|appointment-booking) echo "agent-appointment-booking" ;;
    3|outbound|outbound-telephony) echo "agent-outbound-telephony" ;;
    *)
      echo "Unbekannter Agent: $1 (erlaubt: 1, 2, 3, all)" >&2
      return 1
      ;;
  esac
}

agent_profile() {
  case "$1" in
    1|simple|simple-latency) echo "agent1" ;;
    2|appointment|appointment-booking) echo "agent2" ;;
    3|outbound|outbound-telephony) echo "agent3" ;;
    *)
      echo "Unbekannter Agent: $1 (erlaubt: 1, 2, 3, all)" >&2
      return 1
      ;;
  esac
}

agent_prod_service() {
  case "$1" in
    1|simple|simple-latency) echo "agent-simple-latency" ;;
    2|appointment|appointment-booking) echo "agent-appointment-booking" ;;
    3|outbound|outbound-telephony) echo "agent-outbound-telephony" ;;
    all|all-agents) echo "" ;;
    *)
      echo "Unbekannter Agent: $1 (erlaubt: 1, 2, 3, all)" >&2
      return 1
      ;;
  esac
}

env_value() {
  local key="$1"
  grep -E "^${key}=" .env | tail -n1 | cut -d= -f2-
}

set_env_value() {
  local key="$1"
  local value="$2"
  if grep -qE "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

write_livekit_sip_config() {
  local api_key api_secret
  api_key="$(env_value LIVEKIT_API_KEY)"
  api_secret="$(env_value LIVEKIT_API_SECRET)"

  if [[ -z "$api_key" || -z "$api_secret" ]]; then
    echo "LIVEKIT_API_KEY und LIVEKIT_API_SECRET fehlen in .env." >&2
    return 1
  fi

  {
    printf 'api_key: %s\n' "$api_key"
    printf 'api_secret: %s\n' "$api_secret"
    printf 'ws_url: ws://localhost:7880\n'
    printf 'redis:\n'
    printf '  # livekit-sip läuft im Host-Netzwerk; Redis ist dort über localhost erreichbar.\n'
    printf '  address: 127.0.0.1:6379\n'
    printf 'sip_port: 5060\n'
    printf 'rtp_port: 10000-20000\n'
    printf 'logging:\n'
    printf '  level: info\n'
  } > livekit-sip.generated.yaml
}

detect_public_ipv4() {
  local ip=""
  for url in \
    "https://ifconfig.me" \
    "https://api.ipify.org" \
    "https://ipv4.icanhazip.com"
  do
    ip="$(curl -4 -fsS --max-time 5 "$url" 2>/dev/null | tr -d '[:space:]' || true)"
    if [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
      echo "$ip"
      return 0
    fi
  done
  return 1
}

configure_sslip_domains() {
  local current_app current_lk current_url ip dashed app_domain lk_domain
  current_app="$(env_value APP_DOMAIN)"
  current_lk="$(env_value LIVEKIT_DOMAIN)"
  current_url="$(env_value LIVEKIT_URL)"

  if [[ "$current_app" != *"meine-domain.de"* && "$current_lk" != *"meine-domain.de"* && "$current_url" == wss://* ]]; then
    echo "→ Nutze bestehende Domains aus .env:"
    echo "  Frontend: https://${current_app}"
    echo "  LiveKit:  wss://${current_lk}"
    return 0
  fi

  echo "→ Ermittle öffentliche IPv4 für sslip.io..."
  ip="$(detect_public_ipv4)" || {
    echo "Konnte keine öffentliche IPv4 ermitteln. Setze APP_DOMAIN/LIVEKIT_DOMAIN manuell in .env." >&2
    return 1
  }

  dashed="${ip//./-}"
  app_domain="voice-${dashed}.sslip.io"
  lk_domain="lk-${dashed}.sslip.io"

  set_env_value APP_DOMAIN "$app_domain"
  set_env_value LIVEKIT_DOMAIN "$lk_domain"
  set_env_value LIVEKIT_URL "wss://${lk_domain}"

  echo "✓ sslip.io-Domains in .env gesetzt:"
  echo "  Frontend: https://${app_domain}"
  echo "  LiveKit:  wss://${lk_domain}"
}

if [[ ! -f .env ]]; then
  echo "⚠️  .env fehlt. Erst generieren:"
  echo "    ./scripts/generate-keys.sh"
  echo "    # dann .env mit Provider-Keys füllen"
  exit 1
fi

case "${1:-up}" in
  setup|build)
    TARGET="${2:-infra}"
    if [[ "$TARGET" == "all" || "$TARGET" == "all-agents" ]]; then
      echo "→ Baue alle Agent-Images (nur wenn du wirklich alle drei brauchst)..."
      $COMPOSE --profile all-agents build agent-simple-latency agent-appointment-booking agent-outbound-telephony
      echo
      echo "→ Lege alle Agent-Container an (ohne sie zu starten)..."
      $COMPOSE --profile all-agents up --no-start agent-simple-latency agent-appointment-booking agent-outbound-telephony
      echo
      echo "✓ Alle Agents vorbereitet. Infra starten:"
      echo "    ./start.sh"
      exit 0
    fi

    if [[ "$TARGET" != "infra" ]]; then
      SERVICE="$(agent_service "$TARGET")"
      PROFILE="$(agent_profile "$TARGET")"
      echo "→ Baue nur $SERVICE..."
      $COMPOSE --profile "$PROFILE" build "$SERVICE"
      echo
      echo "→ Lege Agent-Container an (ohne ihn zu starten)..."
      $COMPOSE --profile "$PROFILE" up --no-start "$SERVICE"
      echo
      echo "✓ Agent vorbereitet. Infra starten:"
      echo "    ./start.sh"
      exit 0
    fi

    echo "→ Baue Frontend-Image für die lokale Infrastruktur..."
    $COMPOSE build frontend
    echo
    echo "✓ Infrastruktur vorbereitet. Jetzt starten:"
    echo "    ./start.sh"
    echo
    echo "Agents einzeln vorbereiten, wenn du sie brauchst:"
    echo "    ./start.sh setup 1   # Simple Latency"
    echo "    ./start.sh setup 2   # Termin-Assistent"
    echo "    ./start.sh setup 3   # Outbound-Anruf"
    ;;
  sslip|setup-sslip)
    configure_sslip_domains
    ;;
  vps|prod|production)
    TARGET="${2:-1}"
    configure_sslip_domains
    if [[ "$TARGET" == "all" || "$TARGET" == "all-agents" ]]; then
      write_livekit_sip_config
      echo "→ Starte VPS-Produktion mit allen Agents..."
      $PROD_COMPOSE --profile all-agents up -d --build
    else
      SERVICE="$(agent_prod_service "$TARGET")"
      PROFILE="$(agent_profile "$TARGET")"
      echo "→ Starte VPS-Produktion mit $SERVICE..."
      if [[ "$TARGET" == "3" || "$TARGET" == "outbound" || "$TARGET" == "outbound-telephony" ]]; then
        write_livekit_sip_config
        $PROD_COMPOSE --profile "$PROFILE" up -d --build caddy redis livekit-server livekit-sip frontend "$SERVICE"
      else
        $PROD_COMPOSE --profile "$PROFILE" up -d --build caddy redis livekit-server frontend "$SERVICE"
      fi
    fi
    echo
    echo "✓ VPS gestartet:"
    echo "  Frontend: https://$(env_value APP_DOMAIN)"
    echo "  LiveKit:  wss://$(env_value LIVEKIT_DOMAIN)"
    ;;
  vps-stop|prod-stop|stop-agent)
    TARGET="${2:-all}"
    if [[ "$TARGET" == "all" || "$TARGET" == "all-agents" ]]; then
      echo "→ Stoppe alle VPS-Agent-Container..."
      $PROD_COMPOSE --profile all-agents stop agent-simple-latency agent-appointment-booking agent-outbound-telephony
    else
      SERVICE="$(agent_prod_service "$TARGET")"
      PROFILE="$(agent_profile "$TARGET")"
      echo "→ Stoppe $SERVICE..."
      $PROD_COMPOSE --profile "$PROFILE" stop "$SERVICE"
    fi
    ;;
  agent-setup|prepare-agent)
    TARGET="${2:-}"
    if [[ -z "$TARGET" ]]; then
      echo "Usage: $0 agent-setup <1|2|3|all>"
      exit 1
    fi
    "$0" setup "$TARGET"
    ;;
  up|start|"")
    echo "→ Starte Infrastructure (LiveKit + Redis + Frontend)..."
    $COMPOSE up -d
    echo
    echo "✓ Frontend: http://localhost:3000"
    echo "  Im Browser kannst du jeden Agent einzeln starten/stoppen."
    echo "  Logs:         ./start.sh logs"
    echo "  Stop:         ./start.sh stop"
    ;;
  -f|foreground)
    $COMPOSE up
    ;;
  stop|down)
    echo "→ Stoppe alles (Infra + evtl. laufende Agents)..."
    $COMPOSE --profile all-agents down
    ;;
  logs)
    $COMPOSE logs -f
    ;;
  agent-logs)
    NAME="${2:-}"
    if [[ -z "$NAME" ]]; then
      echo "Usage: $0 agent-logs <1|2|3>"
      exit 1
    fi
    docker logs -f "voice-agent-$NAME"
    ;;
  status|ps)
    $COMPOSE --profile all-agents ps
    ;;
  *)
    echo "Usage: $0 [setup [infra|1|2|3|all]|sslip|vps [1|2|3|all]|vps-stop [1|2|3|all]|up|stop|logs|status|agent-logs N]"
    exit 1
    ;;
esac
