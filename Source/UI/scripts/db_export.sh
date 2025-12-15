#!/usr/bin/env bash
set -euo pipefail

# Usage: ./db_export.sh [output-file] [container-name]
# Default output-file: flood_prediction.dump
# Default container-name: flood-postgres

OUT_FILE="${1:-flood_prediction.dump}"
CONTAINER_NAME="${2:-flood-postgres}"

echo "Exporting database 'flood_prediction' from container '${CONTAINER_NAME}' to '${OUT_FILE}'..."

# Use pg_dump in custom format (-Fc) so restore via pg_restore is easy and supports blobs
docker exec -t "${CONTAINER_NAME}" pg_dump -U flood_user -d flood_prediction -Fc > "${OUT_FILE}"

echo "Export complete: ${OUT_FILE}"
