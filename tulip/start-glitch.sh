#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
  elif [ -f .env.glitch.example ]; then
    cp .env.glitch.example .env
  else
    echo "No .env found and no .env.example template." >&2
    exit 1
  fi
  echo "Created .env — edit TEAM_ID, VM_IP, TICK_START, passwords, then re-run."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

mkdir -p "${TRAFFIC_DIR_HOST:-./services/test_pcap}"
mkdir -p "${EXPLOITS_DIR_HOST:-./exploits}"

docker compose -f docker-compose.yml -f docker-compose.glitch.yml up -d --build

echo ""
echo "Tulip UI:    http://$(hostname -I | awk '{print $1}'):3000"
echo "Gateway UI:  http://$(hostname -I | awk '{print $1}'):8000"
echo "Put exploits in: ${EXPLOITS_DIR_HOST:-./exploits}"
