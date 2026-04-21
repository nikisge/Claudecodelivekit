#!/usr/bin/env bash
# Generiert einen LiveKit API-Key + Secret und schreibt sie in .env.
# Nutzung: ./scripts/generate-keys.sh

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "→ .env aus .env.example erstellt"
fi

API_KEY="APIk$(openssl rand -hex 6)"
API_SECRET="$(openssl rand -hex 32)"

# Ersetze nur die zwei Zeilen, ohne den Rest zu zerstören
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s|^LIVEKIT_API_KEY=.*|LIVEKIT_API_KEY=${API_KEY}|" .env
  sed -i '' "s|^LIVEKIT_API_SECRET=.*|LIVEKIT_API_SECRET=${API_SECRET}|" .env
else
  sed -i "s|^LIVEKIT_API_KEY=.*|LIVEKIT_API_KEY=${API_KEY}|" .env
  sed -i "s|^LIVEKIT_API_SECRET=.*|LIVEKIT_API_SECRET=${API_SECRET}|" .env
fi

echo "→ LiveKit-Keys in .env eingetragen:"
echo "   API_KEY=${API_KEY}"
echo "   API_SECRET=${API_SECRET:0:12}… (gekürzt)"
