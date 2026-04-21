#!/usr/bin/env bash
# One-Command-Workflow für Zuschauer.
#
# Typischer Ablauf:
#   ./start.sh setup   → einmalig: alle Agent-Images bauen (dauert ~5 Min)
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

if [[ ! -f .env ]]; then
  echo "⚠️  .env fehlt. Erst generieren:"
  echo "    ./scripts/generate-keys.sh"
  echo "    # dann .env mit Provider-Keys füllen"
  exit 1
fi

case "${1:-up}" in
  setup|build)
    echo "→ Baue Agent-Images (einmalig, ~5 Min beim ersten Mal)..."
    $COMPOSE --profile all-agents build
    echo
    echo "→ Lege Agent-Container an (ohne sie zu starten)..."
    # Ohne diesen Schritt zeigt das Frontend alle Kacheln als "missing",
    # weil getAgentState() via docker inspect prüft und die Container
    # noch nicht existieren.
    $COMPOSE --profile all-agents up --no-start
    echo
    echo "✓ Setup fertig. Jetzt Infra starten:"
    echo "    ./start.sh"
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
    echo "Usage: $0 [setup|up|stop|logs|status|agent-logs N]"
    exit 1
    ;;
esac
