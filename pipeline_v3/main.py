"""Orchestrate the entire pipeline_v3 workflow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
PIPELINE_STEPS = PIPELINE_DIR / "pipeline"

PREPROCESSING_STEPS = [
    "01_load_inputs.py",
    "02_resample_interpolate.py",
    "03_feature_engineering.py",
    "04_split_train_val_test.py",
]
SPLIT_STEP = "04_split_train_val_test.py"
TRAIN_STEP = "05_train_models.py"
PREDICTION_STEPS = [
    "06_predict_and_ensemble.py",
    "07_export_results.py",
]


def run_script(script_name: str) -> None:
    script_path = PIPELINE_STEPS / script_name
    cmd = [sys.executable, str(script_path)]
    print("\n" + "=" * 80)
    print("Running", script_path)
    print("=" * 80)
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="pipeline_v3 runner")
    parser.add_argument("--skip-preprocessing", action="store_true", help="Skip steps 01-04")
    parser.add_argument("--skip-training", action="store_true", help="Skip step 05")
    parser.add_argument("--skip-prediction", action="store_true", help="Skip steps 06-07")
    parser.add_argument(
        "--skip-splitting",
        action="store_true",
        help="Skip step 04 even when preprocessing runs",
    )
    parser.add_argument(
        "--inference-only",
        action="store_true",
        help="Run steps 01-03 plus prediction/export using existing models",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.inference_only:
        args.skip_preprocessing = False
        args.skip_splitting = True
        args.skip_training = True

    if not args.skip_preprocessing:
        for script in PREPROCESSING_STEPS:
            if getattr(args, "skip_splitting", False) and script == SPLIT_STEP:
                print("Skipping dataset split step (04)")
                continue
            run_script(script)
    else:
        print("Skipping preprocessing phase")

    if not args.skip_training:
        run_script(TRAIN_STEP)
    else:
        print("Skipping training phase")

    if not args.skip_prediction:
        for script in PREDICTION_STEPS:
            run_script(script)
    else:
        print("Skipping prediction/export phase")


if __name__ == "__main__":
    main()
