"""Shared helpers for the pipeline_v3 workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

PIPELINE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_ROOT.parent
CONFIG_DIR = PIPELINE_ROOT / "configs"
PROCESSED_DIR = PIPELINE_ROOT / "processed_data"
MODELS_DIR = PIPELINE_ROOT / "models"
OUTPUTS_DIR = PIPELINE_ROOT / "outputs"
TRAIN_SPLIT_DIR = PROCESSED_DIR / "train_val_test_split"
RAW_DIR = PROCESSED_DIR / "raw_inputs"
PREDICTIONS_DIR = PROCESSED_DIR / "predictions"


def ensure_dir(path: Path) -> Path:
    """Create *path* (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_metadata() -> Dict[str, Any]:
    return load_json(CONFIG_DIR / "metadata.json")


def load_hyperparameters() -> Dict[str, Any]:
    return load_json(CONFIG_DIR / "hyperparameters.json")


def save_dataframe(df, destination: Path, *, index: bool = False) -> None:
    ensure_dir(destination.parent)
    df.to_csv(destination, index=index)