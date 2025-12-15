import pandas as pd
import numpy as np
import argparse
import os
import joblib
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
args = parser.parse_args()

LEAD_TIME = args.days
DATA_DIR = f"Data/processed/L{LEAD_TIME}d"
MODEL_DIR = f"Models/Data-Driven-Models/L{LEAD_TIME}d/models"
RESULTS_DIR = f"Models/Data-Driven-Models/L{LEAD_TIME}d"

print("=" * 70)
print(f"STEP 07: EVALUATING ON TEST SET (L{LEAD_TIME}d)")
print("=" * 70)

# 1. Load Test Data
test = pd.read_csv(f"{DATA_DIR}/test.csv")
EXCLUDE = ['date', 'time', 'target_level_max', 'target_level_mean',
           'target_level_min', 'target_level_std', 'target_level',
           'is_flood', 'is_major_flood']
features = [c for c in test.columns if c not in EXCLUDE]
X_test = test[features]
y_test = test['target_level_max']

preds = {}

# 2. Baseline: Persistence
# Logic: Prediction = Target from N days ago
lag_col = f"target_lag{LEAD_TIME}d"
if lag_col in X_test.columns:
    preds['Persistence'] = X_test[lag_col].fillna(method='ffill')
else:
    print(f"  ⚠️ Warning: {lag_col} not found. Using naive zeros.")
    preds['Persistence'] = np.zeros(len(y_test))

# 3. XGBoost
xgb_model = xgb.Booster()
xgb_model.load_model(f"{MODEL_DIR}/xgb_q90.json")

dtest = xgb.DMatrix(X_test)
preds['XGBoost'] = xgb_model.predict(dtest)


# 4. Bayesian
bayes_model = joblib.load(f"{MODEL_DIR}/bayes_model.pkl")
bayes_scaler = joblib.load(f"{MODEL_DIR}/bayes_scaler.pkl")
X_test_bayes = bayes_scaler.transform(X_test)
mu, sigma = bayes_model.predict(X_test_bayes, return_std=True)
preds['Bayesian'] = mu + (2 * sigma)  # Safety Bound


# 5. LSTM
def quantile_loss(q, y_true, y_pred):
    return tf.reduce_mean(tf.maximum(q * (y_true - y_pred), (q - 1) * (y_true - y_pred)))


lstm_model = load_model(f"{MODEL_DIR}/lstm_q90.h5", custom_objects={'<lambda>': lambda y, p: quantile_loss(0.90, y, p)})
scaler_x = joblib.load(f"{MODEL_DIR}/lstm_scaler_x.pkl")
scaler_y = joblib.load(f"{MODEL_DIR}/lstm_scaler_y.pkl")

X_test_sc = scaler_x.transform(X_test)
X_test_lstm = X_test_sc.reshape((X_test_sc.shape[0], 1, X_test_sc.shape[1]))
pred_sc = lstm_model.predict(X_test_lstm, verbose=0)
preds['LSTM'] = scaler_y.inverse_transform(pred_sc).flatten()

# 6. Ensemble (Safety Max)
stack = np.column_stack([preds['XGBoost'], preds['Bayesian'], preds['LSTM']])
preds['Ensemble'] = np.median(stack, axis=1)

# 7. Metrics Calculation
metrics = []
FLOOD = 30.0

for name, p in preds.items():
    rmse = np.sqrt(mean_squared_error(y_test, p))
    bias = np.mean(p - y_test)

    # Safety Stats
    actual_flood = y_test >= FLOOD
    pred_flood = p >= FLOOD

    missed = (actual_flood & ~pred_flood).sum()
    false_alarms = (~actual_flood & pred_flood).sum()

    metrics.append({
        'Lead Time': f"{LEAD_TIME} Days",
        'Model': name,
        'RMSE': round(rmse, 2),
        'Bias': round(bias, 2),
        'Missed Floods': missed,
        'False Alarms': false_alarms
    })

df_metrics = pd.DataFrame(metrics)
print(df_metrics)
df_metrics.to_csv(f"{RESULTS_DIR}/scorecard.csv", index=False)
print(f"  ✓ Saved scorecard to {RESULTS_DIR}/scorecard.csv")