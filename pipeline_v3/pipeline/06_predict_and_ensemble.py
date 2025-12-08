"""Generate forecasts for each lead and apply the safety-first ensemble."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import keras
import numpy as np
import pandas as pd
import tensorflow as tf

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_v3.utils import (
    MODELS_DIR,
    PREDICTIONS_DIR,
    TRAIN_SPLIT_DIR,
    ensure_dir,
    load_hyperparameters,
)

TARGET_COL = "target_level_max"


def _quantile_loss(q: float):
    def loss(y_true, y_pred):
        error = y_true - y_pred
        return tf.reduce_mean(tf.maximum(q * error, (q - 1) * error))

    return loss


def _load_feature_list(model_dir):
    metadata_path = model_dir / "model_metadata.json"
    with metadata_path.open("r", encoding="utf-8") as fp:
        meta = json.load(fp)
    return meta["features"], meta.get("hyperparameters", {})


def _predict_for_lead(lead: int) -> pd.DataFrame:
    split_dir = TRAIN_SPLIT_DIR / f"L{lead}d"
    test = pd.read_csv(split_dir / "test.csv")
    model_dir = MODELS_DIR / f"L{lead}d"

    features, hparams = _load_feature_list(model_dir)
    X = test[features]
    y = test[TARGET_COL]

    xgb_model = joblib.load(model_dir / "xgboost_model.pkl")
    pred_xgb = xgb_model.predict(X)

    bayes_model = joblib.load(model_dir / "bayesian_ridge.pkl")
    bayes_scaler = joblib.load(model_dir / "bayesian_scaler.pkl")
    mu, sigma = bayes_model.predict(bayes_scaler.transform(X), return_std=True)
    pred_bayes = mu + (2 * sigma)

    lstm_model: Any = keras.models.load_model(
        model_dir / "lstm_model.keras",
        custom_objects={"loss": _quantile_loss(hparams.get("lstm", {}).get("quantile", 0.9))},
    )
    lstm_scaler_x = joblib.load(model_dir / "lstm_scaler_x.pkl")
    lstm_scaler_y = joblib.load(model_dir / "lstm_scaler_y.pkl")
    X_seq = lstm_scaler_x.transform(X).reshape((-1, 1, X.shape[1]))
    pred_lstm = lstm_scaler_y.inverse_transform(lstm_model.predict(X_seq, verbose=0)).flatten()

    stack = np.column_stack([pred_xgb, pred_lstm, pred_bayes])
    p_final = np.max(stack, axis=1)

    output = pd.DataFrame(
        {
            "date": test["date"],
            TARGET_COL: y,
            "P_XGB": pred_xgb,
            "P_LSTM": pred_lstm,
            "P_Bayesian": pred_bayes,
            "P_final": p_final,
        }
    )
    return output


def main() -> None:
    hyperparams = load_hyperparameters()
    leads = hyperparams.get("lead_times", [1])
    ensure_dir(PREDICTIONS_DIR)

    for lead in leads:
        predictions = _predict_for_lead(lead)
        path = PREDICTIONS_DIR / f"L{lead}d_test_predictions.csv"
        predictions.to_csv(path, index=False)
        print(f"Saved predictions for L{lead}d -> {path}")


if __name__ == "__main__":
    main()
