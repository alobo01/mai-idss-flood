"""Train XGBoost, Bayesian Ridge, and LSTM models for each lead time."""

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
import xgboost as xgb
from keras import Sequential
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Dropout, LSTM
from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import MinMaxScaler, StandardScaler

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_v3.utils import MODELS_DIR, TRAIN_SPLIT_DIR, ensure_dir, load_hyperparameters

TARGET_COL = "target_level_max"
EXCLUDE_COLS = {
    "date",
    "time",
    "target_level_mean",
    "target_level_min",
    "target_level_std",
    "is_flood",
    "is_major_flood",
}


def _quantile_loss(q: float):
    def loss(y_true, y_pred):
        error = y_true - y_pred
        return tf.reduce_mean(tf.maximum(q * error, (q - 1) * error))

    return loss


def _get_features(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col not in EXCLUDE_COLS and col != TARGET_COL]


def _train_xgb(X_train, y_train, X_val, y_val, params):
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


def _train_bayesian(X_train, y_train, X_val, y_val, params):
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    bayes = BayesianRidge(**params)
    bayes.fit(X_train_s, y_train)
    return bayes, scaler


def _train_lstm(X_train, y_train, X_val, y_val, params):
    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()

    X_train_s = scaler_x.fit_transform(X_train)
    X_val_s = scaler_x.transform(X_val)
    y_train_s = scaler_y.fit_transform(y_train.values.reshape(-1, 1))
    y_val_s = scaler_y.transform(y_val.values.reshape(-1, 1))

    X_train_seq = X_train_s.reshape((-1, 1, X_train_s.shape[1]))
    X_val_seq = X_val_s.reshape((-1, 1, X_val_s.shape[1]))

    model = Sequential(
        [
            LSTM(params["units"], input_shape=(1, X_train_s.shape[1]), return_sequences=False),
            Dropout(params["dropout"]),
            Dense(params["dense_units"], activation="relu"),
            Dense(1),
        ]
    )
    optimizer: Any = keras.optimizers.Adam(learning_rate=params["learning_rate"])
    model.compile(optimizer=optimizer, loss=_quantile_loss(params["quantile"]))

    early_stop = EarlyStopping(patience=params["patience"], restore_best_weights=True, monitor="val_loss")
    verbose_flag: Any = 0
    model.fit(
        X_train_seq,
        y_train_s,
        validation_data=(X_val_seq, y_val_s),
        epochs=params["epochs"],
        batch_size=params["batch_size"],
        verbose=verbose_flag,
        callbacks=[early_stop],
    )
    return model, scaler_x, scaler_y


def main() -> None:
    hyperparams = load_hyperparameters()
    leads = hyperparams.get("lead_times", [1])

    for lead in leads:
        split_dir = TRAIN_SPLIT_DIR / f"L{lead}d"
        train = pd.read_csv(split_dir / "train.csv")
        val = pd.read_csv(split_dir / "val.csv")

        features = _get_features(train)
        X_train, y_train = train[features], train[TARGET_COL]
        X_val, y_val = val[features], val[TARGET_COL]

        model_dir = ensure_dir(MODELS_DIR / f"L{lead}d")

        xgb_model = _train_xgb(X_train, y_train, X_val, y_val, hyperparams["xgboost"])
        joblib.dump(xgb_model, model_dir / "xgboost_model.pkl")

        bayes_model, bayes_scaler = _train_bayesian(X_train, y_train, X_val, y_val, hyperparams["bayesian_ridge"])
        joblib.dump(bayes_model, model_dir / "bayesian_ridge.pkl")
        joblib.dump(bayes_scaler, model_dir / "bayesian_scaler.pkl")

        lstm_model, lstm_scaler_x, lstm_scaler_y = _train_lstm(
            X_train,
            y_train,
            X_val,
            y_val,
            hyperparams["lstm"],
        )
        lstm_model.save(model_dir / "lstm_model.keras", overwrite=True)
        joblib.dump(lstm_scaler_x, model_dir / "lstm_scaler_x.pkl")
        joblib.dump(lstm_scaler_y, model_dir / "lstm_scaler_y.pkl")

        metadata = {
            "features": features,
            "target": TARGET_COL,
            "hyperparameters": hyperparams,
        }
        with (model_dir / "model_metadata.json").open("w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2)

        print(f"Trained models for L{lead}d horizon -> {model_dir}")


if __name__ == "__main__":
    main()
