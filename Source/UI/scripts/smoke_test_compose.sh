#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-UI/docker-compose.yml}"

echo "Running compose smoke tests using ${COMPOSE_FILE}"

backend_json() {
  local path="$1"
  docker compose -f "${COMPOSE_FILE}" exec -T backend python - <<PY
import json
import sys
import urllib.request

url = "http://localhost:8000${path}"
req = urllib.request.Request(url, headers={"Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        print(body)
except Exception as e:
    print(f"ERROR requesting {url}: {e}", file=sys.stderr)
    sys.exit(1)
PY
}

assert_contains() {
  local name="$1"
  local haystack="$2"
  local needle="$3"
  if [[ "${haystack}" != *"${needle}"* ]]; then
    echo "FAIL: ${name} did not contain: ${needle}" >&2
    echo "${haystack}" >&2
    exit 1
  fi
}

echo "[1/4] GET /health"
health="$(backend_json "/health")"
assert_contains "/health" "${health}" "\"status\""
assert_contains "/health" "${health}" "healthy"

echo "[2/4] GET /zones"
zones="$(backend_json "/zones")"
assert_contains "/zones" "${zones}" "\"success\""
assert_contains "/zones" "${zones}" "\"rows\""

echo "[3/4] GET /resource-types"
resources="$(backend_json "/resource-types")"
assert_contains "/resource-types" "${resources}" "\"rows\""

echo "[4/4] GET /rule-based/dispatch"
dispatch="$(backend_json "/rule-based/dispatch?total_units=12&mode=fuzzy&lead_time=1&max_units_per_zone=6")"
assert_contains "/rule-based/dispatch" "${dispatch}" "\"zones\""
assert_contains "/rule-based/dispatch" "${dispatch}" "\"resource_metadata\""

echo "OK: compose smoke tests passed"

