#!/usr/bin/env bash
set -euo pipefail

set -a
# shellcheck disable=SC1091
source .env
set +a

if [ -n "${FLAGID_SCRAPE:-}" ]; then
  docker compose -f docker-compose.yml -f docker-compose-flagid.yml up
else
  docker compose up
fi
