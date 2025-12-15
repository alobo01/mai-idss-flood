# Backend API Testing (docker-compose)

## One-shot full test run
```bash
docker build -t flood-backend-test Source/frontend/python_backend
docker compose -f Source/frontend/docker-compose.test.yml \
  up --abort-on-container-exit --exit-code-from backend-test --remove-orphans
```
This starts a throwaway PostGIS container, seeds schema/init data, runs the FastAPI backend tests (pytest), and exits with the test status.

## What’s in the stack
- `postgres-test` (postgis/postgis:15-3.3) seeded by `Source/frontend/database/init/01-schema.sql` and `02-migrate-mock-data-fixed.sql` (the older mock-data file is disabled to avoid conflicts).
- `backend-test` (image `flood-backend-test`) runs `pytest -v tests/`.

## Notes
- Pipeline rule-based bridge endpoint `/api/rule-based/pipeline` is included; if the Models package is missing in an image, it returns HTTP 501 instead of crashing.
- SQLAlchemy model columns formerly named `metadata` were renamed to `meta` to avoid reserved-name collisions.
- Communications/Plans inserts cast JSON correctly for Postgres (`CAST(:payload AS jsonb)`).
- Gauges query returns GeoJSON and trend as before; risks, alerts, resources, and zones endpoints are covered by tests.
