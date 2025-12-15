# Real-data Simulation Pipeline (St. Louis)

## Generate risk snapshots from the training/test CSV
```
python Source/frontend/backend/scripts/generate_risk_from_csv.py \
  Data/processed/L1d/test.csv
```
- Reads the CSV, scales `target_level_max` to a global flood probability, maps it to per-zone probabilities using `Models.zone_builder`, and writes `risk_*.json` into:
  - `Source/frontend/backend/`
  - `Source/frontend/public/mock/`
- Emits `Source/frontend/src/hooks/riskTimeline.generated.ts` so the UI simulation replays the same timeline (1 hour every 15 seconds).

## Seed the database with the generated snapshots
```
docker run --rm --network host \
  -e DB_HOST=localhost -e DB_PORT=5433 \
  -v "$(pwd)/Source/frontend/backend:/srv" -w /srv node:20-alpine \
  sh -c "npm ci && node scripts/seed.js"
```

## Run smoke tests with curl
Make sure the API is running on port 18080, then:
```
Source/frontend/backend/scripts/curl_smoketest.sh
```
Expected: all checks print and exit 0 (zones/risk/allocations/alerts/resources/gauges/comms/plan).
