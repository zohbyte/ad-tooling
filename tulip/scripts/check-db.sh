#!/usr/bin/env sh
set -eu

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.glitch.yml"
cd "$(dirname "$0")/.."

echo "=== Timescale tables ==="
docker compose $COMPOSE_FILES exec timescale \
  psql -U tulip -d tulip -c '\dt' || true

echo ""
echo "=== schema-init logs ==="
docker compose $COMPOSE_FILES logs schema-init | tail -20

echo ""
echo "=== assembler capture mode ==="
docker compose $COMPOSE_FILES logs assembler | tail -15
