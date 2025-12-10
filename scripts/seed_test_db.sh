#!/usr/bin/env bash
set -euo pipefail

# Configuration
CONTAINER_NAME=${CONTAINER_NAME:-flood-postgres-test}
HOST_PORT=${HOST_PORT:-5434}
DB_NAME=${DB_NAME:-flood_prediction}
DB_USER=${DB_USER:-flood_user}
DB_PASSWORD=${DB_PASSWORD:-flood_password}
IMAGE=${IMAGE:-postgis/postgis:15-3.3}
SCHEMA_FILE="Source/frontend/database/init/01-schema.sql"
DATA_FILE="Source/frontend/database/init/02-migrate-mock-data-fixed.sql"

# Start container if not running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Starting existing container ${CONTAINER_NAME}..."
    docker start "${CONTAINER_NAME}" >/dev/null
  else
    echo "Creating PostGIS container ${CONTAINER_NAME} on host port ${HOST_PORT}..."
    docker run -d \
      --name "${CONTAINER_NAME}" \
      -p "${HOST_PORT}:5432" \
      -e POSTGRES_DB="${DB_NAME}" \
      -e POSTGRES_USER="${DB_USER}" \
      -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
      ${IMAGE} >/dev/null
  fi
fi

# Wait for Postgres to accept connections
until docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  echo "Waiting for database to become ready..."
  sleep 2
done

echo "Database is ready; applying schema and seed data..."

# Apply schema
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${SCHEMA_FILE}"

# Apply data (safe upsert by clearing existing rows to avoid duplicates)
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" <<'SQL'
TRUNCATE deployments, communications, alerts, resources, damage_assessments, assets, risk_assessments, zones, gauges, admin_users, admin_risk_thresholds, response_plans CASCADE;
SQL

docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${DATA_FILE}"

echo "Seed complete. Row counts:"
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 'zones' tbl, count(*) FROM zones UNION ALL SELECT 'resources', count(*) FROM resources UNION ALL SELECT 'alerts', count(*) FROM alerts UNION ALL SELECT 'risk_assessments', count(*) FROM risk_assessments;"

echo "Done. Connect with: psql postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${HOST_PORT}/${DB_NAME}"
