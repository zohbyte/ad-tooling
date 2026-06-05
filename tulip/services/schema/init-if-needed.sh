#!/bin/sh
set -eu

echo "Waiting for Timescale..."
until pg_isready -h "${PGHOST:-timescale}" -U "${PGUSER:-tulip}" >/dev/null 2>&1; do
  sleep 1
done

if psql -h "${PGHOST:-timescale}" -U "${PGUSER:-tulip}" -d "${PGDATABASE:-tulip}" -tAc \
  "SELECT to_regclass('public.flow')" | grep -q flow; then
  echo "Tulip schema already present."
  exit 0
fi

echo "Applying Tulip schema..."
psql -v ON_ERROR_STOP=1 -h "${PGHOST:-timescale}" -U "${PGUSER:-tulip}" -d "${PGDATABASE:-tulip}" \
  -f /schema/system.sql
psql -v ON_ERROR_STOP=1 -h "${PGHOST:-timescale}" -U "${PGUSER:-tulip}" -d "${PGDATABASE:-tulip}" \
  -f /schema/functions.sql
psql -v ON_ERROR_STOP=1 -h "${PGHOST:-timescale}" -U "${PGUSER:-tulip}" -d "${PGDATABASE:-tulip}" \
  -f /schema/schema.sql
echo "Tulip schema applied."
