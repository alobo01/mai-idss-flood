# Pipeline v2 Usage Guide

## Commands

```bash
python run_pipeline_v2.py                 # run all scenarios defined in pipeline_v2/config.yaml
python run_pipeline_v2.py --scenario data1India --retries 2
```

Each scenario executes two stages:
1. `pipeline_v2/build_inputs.py` – standardizes the processed dataset, applies schema validation, and writes provenance metadata alongside the CSV.
2. `pipeline_v2/run_allocator.py` – loads the standardized file, executes the rule-based model, enforces business rules, and writes allocations plus provenance manifests under `Results/v2/<scenario>/`.

Structured JSON logging is enabled everywhere, so logs can be shipped to any aggregator.

## Configuration Highlights (`pipeline_v2/config.yaml`)

- `paths.processed` – source datasets (notebooks output).
- `paths.standardized` – destination for `_model_input.csv` files.
- `paths.results` – root for allocation outputs and status manifests.
- Scenario-level overrides: `total_units`, `max_units_per_zone`, `zone_config`, `river_level_column`, etc.

## Zone Metadata

Each scenario references a YAML file in `pipeline_v2/zone_configs/`. These files hold:
- vulnerability weights per feature,
- per-zone exposure components,
- probability scaling factors (`pf_weight`),
- hospital counts / critical infrastructure flags.

The loader converts them into `ZoneProfile` objects used during both standardization and business-rule enforcement.

## Business Rules

`pipeline_v2/business_rules.py` enforces:
- Constant total units per timestamp.
- Minimum units reserved for critical infrastructure zones.
- Optional per-zone caps.
- Presence of allocations for every configured zone.

Any violation raises `BusinessRuleError`, which surfaces in the orchestrator status files.

## Provenance

Every build/allocate stage writes a manifest capturing:
- scenario name,
- absolute config path and SHA-256 hash,
- source/standardized file paths and hashes,
- git commit (if available).

This guarantees traceability for downstream auditing.

## Container & CI

- `Dockerfile.pipeline` packages the repo for scheduled executions (`docker run pipeline-v2`).
- `.github/workflows/pipeline.yml` runs pytest + a Docker smoke test on each push/PR.
