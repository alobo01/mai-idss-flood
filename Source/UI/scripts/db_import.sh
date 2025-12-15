#!/usr/bin/env bash
set -euo pipefail

# Usage: ./db_import.sh [dump-file] [container-name]
# Default dump-file: flood_prediction.dump
# Default container-name: flood-postgres

DUMP_FILE="${1:-flood_prediction.dump}"
CONTAINER_NAME="${2:-flood-postgres}"

if [ ! -f "${DUMP_FILE}" ]; then
  echo "Dump file '${DUMP_FILE}' not found on host."
  exit 2
fi

echo "Restoring '${DUMP_FILE}' into database 'flood_prediction' inside container '${CONTAINER_NAME}'..."

# Note: this restores into the existing database. If you need a fresh DB, drop/create first.
docker exec -i "${CONTAINER_NAME}" pg_restore -U flood_user -d flood_prediction -v < "${DUMP_FILE}"

echo "Restore complete."
