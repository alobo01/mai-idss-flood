# Pipeline v2 Architecture (Data → Model → Results)

This document summarizes the improvements required for a production-grade integration layer without modifying the original notebooks. The new implementation lives alongside the legacy scripts and introduces the following building blocks:

1. **Schema validation** – `pipeline_v2/schema.py`
   - Uses declarative column contracts to validate CSV inputs (processed datasets, standardized model inputs, allocator outputs) before any transformation occurs.
   - Exposes reusable `validate_dataframe(name, dataframe, schema)` helper returning detailed error messages.

2. **Scenario-specific zone metadata** – `pipeline_v2/zone_registry.py`
   - Each scenario in `pipeline_v2/config.yaml` points to a dedicated zone definition file (`pipeline_v2/zone_configs/<scenario>.yaml`).
   - Zone files contain vulnerability weights, hospital counts, and optional overrides so non‑St. Louis use cases stop relying on `Models/zone_config.py`.

3. **Business-rule enforcement** – `pipeline_v2/business_rules.py`
   - Adds guardrails (minimum units for critical infrastructure, cap per zone, depot capacity) executed after `allocate_resources`.
   - Violations raise structured exceptions surfaced in reports/logs.

4. **Provenance & structured logging** – `pipeline_v2/provenance.py` + `pipeline_v2/logging_utils.py`
   - Captures git commit, config hash, dataset checksum, runtime timings, and embeds the metadata inside both CSV/JSON outputs.
   - Logging uses JSON lines (timestamp, level, scenario, stage) to feed observability stacks.

5. **Scenario-isolated runner** – `run_pipeline_v2.py`
   - Iterates over scenarios with per-scenario try/except, retries, and status reporting without blocking other runs.
   - Emits success/failure reports plus provenance manifests in `Results/<scenario>/`.

6. **Automated tests** – `tests/test_pipeline_v2.py`
   - Unit tests cover schema validation, registry lookups, business rules, and provenance hashing.

7. **Containerization & CI**
   - `Dockerfile.pipeline` builds a minimal image (Python slim + project deps) for scheduled runs.
   - `.github/workflows/pipeline.yml` executes tests and smoke runs inside the container on each push/PR.

The remainder of the implementation follows this plan.
