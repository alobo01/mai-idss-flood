#!/usr/bin/env bash
set -euo pipefail

# Basic curl smoke tests against a running API (expects port 18080, seeded DB)
BASE=${BASE:-http://localhost:18080/api}

echo "Health..."
curl -sf "$BASE/../health" | jq '.status' | grep -q '"ok"'

echo "Zones..."
curl -sf "$BASE/zones" | jq '.features[0].properties.id' | grep -q '"Z1N"'

echo "Risk (uses latest snapshot)..."
curl -sf "$BASE/risk?timeHorizon=12h" | jq '.[0].thresholdBand' | grep -E '"Low"|"Moderate"|"High"|"Severe"'

echo "Rule-based pipeline allocation..."
curl -sf "$BASE/rule-based/pipeline?global_pf=0.6&total_units=12&mode=crisp" | jq '.allocations | length' | grep -q '[1-9]'

echo "Alerts..."
curl -sf "$BASE/alerts" | jq '.[0].severity' | grep -q '"Severe"'

echo "Resources..."
curl -sf "$BASE/resources" | jq '.crews[0].id' | grep -q '"C-'

echo "Gauges..."
curl -sf "$BASE/gauges" | jq '.[0].trend' | grep -q '"rising"'

echo "Communications..."
curl -sf "$BASE/comms" | jq '.[0].channel' | grep -q '"global"'

echo "Plan..."
curl -sf "$BASE/plan" | jq '.assignments[0].zoneId' | grep -q '"Z'

echo "Smoke tests passed."
