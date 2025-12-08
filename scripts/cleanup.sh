#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say() { printf '[cleanup] %s\n' "$*"; }

say "Removing regenerated Results tree"
rm -rf "$ROOT/Results"
mkdir -p "$ROOT/Results/v2"
touch "$ROOT/Results/.gitkeep"

say "Removing processed datasets"
rm -rf "$ROOT/Data/processed" "$ROOT/Data/processed_v2"
mkdir -p "$ROOT/Data/processed" "$ROOT/Data/processed_v2"
touch "$ROOT/Data/processed/.gitkeep" "$ROOT/Data/processed_v2/.gitkeep"

say "Deleting pipeline artifacts (allocations, summaries, manifests)"
find "$ROOT" -name 'allocations_*.csv' -delete
find "$ROOT" -name 'summary_*.json' -delete
find "$ROOT" -name '*_model_input.csv' -delete
find "$ROOT" -name '*.meta.json' -delete
find "$ROOT" -name '*.manifest.json' -delete
find "$ROOT" -name 'pipeline_status.json' -delete

say "Clearing pytest / python caches"
rm -rf "$ROOT/.pytest_cache" "$ROOT/tests/__pycache__"
find "$ROOT" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$ROOT" -name '*.pyc' -delete
find "$ROOT" -name '*.pyo' -delete

say "Removing local virtualenvs and OS cruft"
rm -rf "$ROOT/venv" "$ROOT/.python-version" "$ROOT/.venv" "$ROOT/env" "$ROOT/.DS_Store"
find "$ROOT" -name '.DS_Store' -delete || true
find "$ROOT" -name 'Thumbs.db' -delete || true

say "Dropping stray logs and debug helpers"
rm -rf "$ROOT/logs" 2>/dev/null || true
rm -f "$ROOT"/*.log "$ROOT"/*.tmp 2>/dev/null || true
rm -f "$ROOT/Source/frontend"/debug_test*.js 2>/dev/null || true

say "Cleanup complete. Recreate venv + rerun tests afterwards."
