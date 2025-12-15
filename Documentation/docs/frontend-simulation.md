# Frontend Simulation (St. Louis)

## What drives the timeline
- `Source/frontend/backend/scripts/generate_risk_from_csv.py` reads `Data/processed/L1d/test.csv`, maps global PF → zone PFs, and writes hourly `risk_*.json` into:
  - `Source/frontend/backend/`
  - `Source/frontend/public/mock/`
- The same script emits `Source/frontend/src/hooks/riskTimeline.generated.ts`, which the UI uses for the playback loop (1 hour simulated every 15 seconds).

## Map defaults
- Center: St. Louis `[38.627, -90.199]`.
- Zones: Z1N, Z1S, Z2, Z3, Z4, ZC (riverfront + inland sets).
- Assets/resources/gauges/alerts/plan data align to these zones in the mocks and DB seed.

## Refresh cycle after new data
1) Run the generator:  
   `python Source/frontend/backend/scripts/generate_risk_from_csv.py Data/processed/L1d/test.csv`
2) Reseed DB (if using Postgres):  
   `docker run --rm --network host -e DB_HOST=localhost -e DB_PORT=5433 -v "$(pwd)/Source/frontend/backend:/srv" -w /srv node:20-alpine sh -c "npm ci && node scripts/seed.js"`
3) Restart backend/frontend containers or dev servers.

## Quick smoke (API-level)
- `Source/frontend/backend/scripts/curl_smoketest.sh` hits health, zones, risk (timeline-driven), pipeline rule-based allocation, alerts, resources, gauges, comms, plan.
