# pipeline_v3 Overview

This document describes the end-to-end flood prediction and response workflow implemented in `pipeline_v3`. It covers the data inputs, preprocessing stages, ML inference, rule-based decision layer, produced outputs, and the directory layout.

## Inputs
- **Raw hydrologic measurements** located in `Data/datasets/` (referenced via `configs/metadata.json`):
  - `river_target_st_louis.csv`: hourly river levels at the target gauge.
  - `river_upstream_grafton.csv`, `river_upstream_hermann.csv`: upstream gauges used as predictors.
- **Weather history** (`weather_history_st_louis.csv.gz`): hourly precipitation, temperature, wind, humidity, soil moisture, etc.
- **Configuration** files under `pipeline_v3/configs/`:
  - `metadata.json`: file paths, flood thresholds, temporal split dates, and rule-based settings.
  - `hyperparameters.json`: model hyperparameters and lead times to run.
- **Trained model artifacts** in `pipeline_v3/models/L*d/` (XGBoost, Bayesian Ridge, LSTM, plus scalers/metadata). Inference-only runs reuse these without retraining.

## Preprocessing Pipeline
1. **01_load_inputs.py** – Loads the raw CSVs, clips everyone to the common time window, timezone-normalizes timestamps, and writes staged hourly files under `processed_data/raw_inputs/`.
2. **02_resample_interpolate.py** – Builds a continuous hourly timeline, interpolates missing target/upstream values, merges weather features, and creates flood indicators. Output: `processed_data/merged_hourly.csv`.
3. **03_feature_engineering.py** – Aggregates hourly data to daily granularity, deriving rolling precipitation/soil metrics and flood labels. Output: `processed_data/engineered_features.csv`.
4. **04_split_train_val_test.py** – (Optional) Adds rolling/lagged predictors for each lead time and writes per-lead datasets plus `train/val/test` splits to `processed_data/train_val_test_split/L*d/`.
5. **05_train_models.py** – (Optional) Fits XGBoost, Bayesian Ridge, and LSTM models for each lead using the engineered features and stores artifacts in `models/L*d/`.

> For production inference you typically run `python pipeline_v3/main.py --inference-only`, which executes steps 01–03, skips 04–05, and then proceeds to predictions with the already trained models.

## Prediction & Rule-Based Layer
6. **06_predict_and_ensemble.py** – Loads the stored models/scalers, scores the test (or latest feature) sets, and produces per-model predictions (`P_XGB`, `P_LSTM`, `P_Bayesian`). The ensemble forecast `P_final` is the element-wise maximum across the three models to emphasize safety.
7. **07_export_results.py** – Computes performance metrics, concatenates predictions across all leads, and (when enabled via `metadata.json`) runs the rule-based allocation model:
   - Converts each `P_final` river-stage forecast into a global flood probability (`global_pf`).
   - Scales risk by zone vulnerability (river proximity, elevation, infrastructure) to obtain zone-level probabilities.
   - Applies the configured allocation mode (`crisp`, `fuzzy`, or `proportional`) to recommend how many response units to allocate per zone/date. Results are written to `outputs/rule_based/L*d_rule_based_allocations.csv`.

## Outputs
- `processed_data/merged_hourly.csv` – clean hourly dataset with target, upstream, and weather signals.
- `processed_data/engineered_features.csv` – daily engineered features used for modeling.
- `processed_data/train_val_test_split/L*d/` – per-lead datasets and splits (if step 04 ran).
- `models/L*d/` – trained ML artifacts (if step 05 ran).
- `processed_data/predictions/L*d_test_predictions.csv` – per-lead prediction tables containing actual targets and the four model columns (`P_XGB`, `P_LSTM`, `P_Bayesian`, `P_final`).
- `outputs/scorecard.csv` – evaluation metrics (RMSE, bias, missed floods, false alarms) for each model/lead.
- `outputs/pfinal_predictions.csv` – all leads combined into one file for downstream visualization/reporting.
- `outputs/rule_based/L*d_rule_based_allocations.csv` – zone-level risk classifications and resource recommendations derived from `P_final`.

## Directory Structure Highlights
```
pipeline_v3/
├── configs/                # metadata + hyperparameters
├── models/                 # trained model artifacts organized by lead
├── pipeline/               # step-by-step scripts (01–07)
├── processed_data/
│   ├── raw_inputs/         # staged CSVs from step 01
│   ├── predictions/        # CSVs from step 06
│   └── train_val_test_split/  # per-lead datasets/splits (step 04)
├── outputs/
│   ├── scorecard.csv
│   ├── pfinal_predictions.csv
│   └── rule_based/         # rule-based allocation exports per lead
├── utils.py                # shared path/config helpers
└── main.py                 # orchestrator with CLI flags (skip steps, inference-only)
```

## Running the Pipeline
- Full training + inference: `python pipeline_v3/main.py`
- Inference-only (no new splits/training, reuse stored models): `python pipeline_v3/main.py --inference-only`
- Customize rule-based behavior by editing `configs/metadata.json` (`rule_based` section: total units, allocation mode, per-zone caps).
