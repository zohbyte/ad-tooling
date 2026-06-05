#!/usr/bin/env bash
# Run on the vulnbox to generate TULIP_SERVICES lines from /services docker-compose files.
set -euo pipefail

SERVICES_DIR="${1:-/services}"

if [ ! -d "$SERVICES_DIR" ]; then
  echo "Services directory not found: $SERVICES_DIR" >&2
  exit 1
fi

echo "# Paste into tulip/.env as TULIP_SERVICES"
for dir in "$SERVICES_DIR"/*; do
  [ -d "$dir" ] || continue
  name="$(basename "$dir")"
  compose="$dir/docker-compose.yml"
  [ -f "$compose" ] || compose="$dir/docker-compose.yaml"
  [ -f "$compose" ] || continue

  ports="$(grep -E '^[[:space:]]*-[[:space:]]*"[0-9]+:' "$compose" 2>/dev/null \
    | sed -E 's/.*"([0-9]+):.*/\1/' | sort -u || true)"

  if [ -z "$ports" ]; then
    ports="$(grep -E '^[[:space:]]*-[[:space:]]*[0-9]+:' "$compose" 2>/dev/null \
      | sed -E 's/.*- *"?([0-9]+):.*/\1/' | sort -u || true)"
  fi

  for port in $ports; do
    echo "$port $name"
  done
done
