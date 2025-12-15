import pandas as pd
import numpy as np
import argparse
import os
import joblib
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import load_model

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
args = parser.parse_args()

LEAD_TIME = args.days
DATA_DIR = f"Data/processed/L{LEAD_TIME}d"
MODEL_DIR = f"Models/Data-Driven-Models/L{LEAD_TIME}d/models"
RESULTS_DIR = f"Models/Data-Driven-Models/Results/L{LEAD_TIME}d"

print("=" * 70)
print(f"STEP 08b: CONFORMAL PREDICTION INTERVALS (L{LEAD_TIME}d)")
print("=" * 70)

# =============================================================================
# 1. LOAD DATA
# =============================================================================

val = pd.read_csv(f"{DATA_DIR}/val.csv")
test = pd.read_csv(f"{DATA_DIR}/test.csv")

EXCLUDE = ['date', 'time', 'target_level_max', 'target_level_mean',
           'target_level_min', 'target_level_std', 'target_level',
           'is_flood', 'is_major_flood']

features = [c for c in val.columns if c not in EXCLUDE]

X_val = val[features]
y_val = val['target_level_max']

X_test = test[features]
y_test = test['target_level_max']

print(f"  Val samples: {len(X_val)}")
print(f"  Test samples: {len(X_test)}")

# =============================================================================
# 2. GENERATE PREDICTIONS FOR ALL QUANTILES
# =============================================================================

print("\n2. Loading models and generating predictions...")

QUANTILES = [0.10, 0.50, 0.90]

predictions = {
    'val': {},
    'test': {}
}

# -----------------------------------------------------------------------------
# A. XGBOOST
# -----------------------------------------------------------------------------

print("  [XGBoost]")
for q in QUANTILES:
    q_label = int(q * 100)
    model = xgb.XGBRegressor()
    model.load_model(f"{MODEL_DIR}/xgb_q{q_label}.json")

    predictions['val'][f'xgb_q{q_label}'] = model.predict(X_val)
    predictions['test'][f'xgb_q{q_label}'] = model.predict(X_test)

# -----------------------------------------------------------------------------
# B. BAYESIAN
# -----------------------------------------------------------------------------

print("  [Bayesian]")
bayes_model = joblib.load(f"{MODEL_DIR}/bayes_model.pkl")
bayes_scaler = joblib.load(f"{MODEL_DIR}/bayes_scaler.pkl")

from scipy.stats import norm

X_val_bayes = bayes_scaler.transform(X_val)
X_test_bayes = bayes_scaler.transform(X_test)

mu_val, sigma_val = bayes_model.predict(X_val_bayes, return_std=True)
mu_test, sigma_test = bayes_model.predict(X_test_bayes, return_std=True)

for q in QUANTILES:
    q_label = int(q * 100)
    z_score = norm.ppf(q)

    predictions['val'][f'bayes_q{q_label}'] = mu_val + z_score * sigma_val
    predictions['test'][f'bayes_q{q_label}'] = mu_test + z_score * sigma_test

# -----------------------------------------------------------------------------
# C. LSTM
# -----------------------------------------------------------------------------

print("  [LSTM]")


def quantile_loss(q):
    def loss(y_true, y_pred):
        e = y_true - y_pred
        return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))

    return loss


scaler_x = joblib.load(f"{MODEL_DIR}/lstm_scaler_x.pkl")
scaler_y = joblib.load(f"{MODEL_DIR}/lstm_scaler_y.pkl")

X_val_sc = scaler_x.transform(X_val).reshape((len(X_val), 1, len(features)))
X_test_sc = scaler_x.transform(X_test).reshape((len(X_test), 1, len(features)))

for q in QUANTILES:
    q_label = int(q * 100)

    model = load_model(
        f"{MODEL_DIR}/lstm_q{q_label}.h5",
        custom_objects={'loss': quantile_loss(q)}
    )

    pred_val_sc = model.predict(X_val_sc, verbose=0)
    pred_test_sc = model.predict(X_test_sc, verbose=0)

    predictions['val'][f'lstm_q{q_label}'] = scaler_y.inverse_transform(pred_val_sc).flatten()
    predictions['test'][f'lstm_q{q_label}'] = scaler_y.inverse_transform(pred_test_sc).flatten()

# =============================================================================
# 3. CREATE ENSEMBLE PREDICTIONS
# =============================================================================

print("\n3. Creating ensemble predictions...")

for split in ['val', 'test']:
    for q_label in [10, 50, 90]:
        # Stack predictions from all 3 models
        stack = np.column_stack([
            predictions[split][f'xgb_q{q_label}'],
            predictions[split][f'bayes_q{q_label}'],
            predictions[split][f'lstm_q{q_label}']
        ])

        # Ensemble strategy depends on quantile
        if q_label == 10:
            # Lower bound: use minimum (most conservative lower)
            predictions[split][f'ensemble_q{q_label}'] = np.min(stack, axis=1)
        elif q_label == 50:
            # Median: use median
            predictions[split][f'ensemble_q{q_label}'] = np.median(stack, axis=1)
        elif q_label == 90:
            # Upper bound: use maximum (most conservative upper)
            predictions[split][f'ensemble_q{q_label}'] = np.max(stack, axis=1)

print("  ✓ Ensemble predictions created")

# =============================================================================
# 4. CONFORMAL CALIBRATION
# =============================================================================

print("\n4. Applying conformal calibration...")

# Use median predictions for calibration
ensemble_q50_val = predictions['val']['ensemble_q50']
ensemble_q50_test = predictions['test']['ensemble_q50']

# Calculate residuals on validation set
residuals_val = np.abs(y_val.values - ensemble_q50_val)

# Conformal quantile for 80% coverage (α = 0.20)
ALPHA = 0.20
n_cal = len(residuals_val)

# Adjusted quantile for finite sample correction
adjusted_quantile = np.ceil((n_cal + 1) * (1 - ALPHA)) / n_cal
conformal_correction = np.quantile(residuals_val, adjusted_quantile)

print(f"  Conformal correction: {conformal_correction:.2f} ft")
print(f"  Target coverage: {(1 - ALPHA) * 100:.0f}%")

# Apply conformal adjustment to test set
predictions['test']['conformal_lower'] = (
        predictions['test']['ensemble_q10'] - conformal_correction
)
predictions['test']['conformal_upper'] = (
        predictions['test']['ensemble_q90'] + conformal_correction
)
predictions['test']['conformal_median'] = ensemble_q50_test

# =============================================================================
# 5. EVALUATE COVERAGE
# =============================================================================

print("\n5. Evaluating prediction intervals...")

# Uncalibrated (raw ensemble)
raw_lower = predictions['test']['ensemble_q10']
raw_upper = predictions['test']['ensemble_q90']
raw_coverage = ((y_test >= raw_lower) & (y_test <= raw_upper)).mean()

# Calibrated (conformal)
conf_lower = predictions['test']['conformal_lower']
conf_upper = predictions['test']['conformal_upper']
conf_coverage = ((y_test >= conf_lower) & (y_test <= conf_upper)).mean()

print(f"\n  Uncalibrated coverage: {raw_coverage:.1%}")
print(f"  Conformal coverage:    {conf_coverage:.1%}")
print(f"  Target:                {(1 - ALPHA) * 100:.0f}%")

# Interval width
raw_width = np.mean(raw_upper - raw_lower)
conf_width = np.mean(conf_upper - conf_lower)

print(f"\n  Uncalibrated width: {raw_width:.2f} ft")
print(f"  Conformal width:    {conf_width:.2f} ft")
print(f"  Increase:           {(conf_width - raw_width):.2f} ft ({(conf_width / raw_width - 1) * 100:.1f}%)")

# =============================================================================
# 6. SAVE PREDICTIONS
# =============================================================================

print("\n6. Saving predictions...")

# Create comprehensive prediction dataframe
pred_df = pd.DataFrame({
    'date': test['date'],
    'actual': y_test,

    # Individual models (q50 only for brevity)
    'xgb_q50': predictions['test']['xgb_q50'],
    'bayes_q50': predictions['test']['bayes_q50'],
    'lstm_q50': predictions['test']['lstm_q50'],

    # Uncalibrated ensemble
    'ensemble_q10': predictions['test']['ensemble_q10'],
    'ensemble_q50': predictions['test']['ensemble_q50'],
    'ensemble_q90': predictions['test']['ensemble_q90'],

    # Conformal intervals
    'conformal_lower': predictions['test']['conformal_lower'],
    'conformal_median': predictions['test']['conformal_median'],
    'conformal_upper': predictions['test']['conformal_upper'],
})

pred_df.to_csv(f"{RESULTS_DIR}/predictions_with_intervals.csv", index=False)
print(f"  ✓ Saved: {RESULTS_DIR}/predictions_with_intervals.csv")

# Save calibration info
calibration_info = {
    'lead_time': LEAD_TIME,
    'alpha': ALPHA,
    'target_coverage': 1 - ALPHA,
    'conformal_correction': conformal_correction,
    'n_calibration': n_cal,
    'test_coverage_uncalibrated': raw_coverage,
    'test_coverage_conformal': conf_coverage,
    'mean_width_uncalibrated': raw_width,
    'mean_width_conformal': conf_width,
}

joblib.dump(calibration_info, f"{RESULTS_DIR}/calibration_info.pkl")
print(f"  ✓ Saved: {RESULTS_DIR}/calibration_info.pkl")

# =============================================================================
# 7. SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("CONFORMAL PREDICTION INTERVALS COMPLETE")
print("=" * 70)

print(f"\n✅ Achieved {conf_coverage:.1%} coverage (target: {(1 - ALPHA) * 100:.0f}%)")

if conf_coverage < (1 - ALPHA - 0.05):
    print("  ⚠️  Under-coverage detected!")
elif conf_coverage > (1 - ALPHA + 0.05):
    print("  💡 Over-conservative (wider intervals)")
else:
    print("  ✓ Coverage within acceptable range")

print(f"\n⏭️  Next: Run 09b_visualize_uncertainty.py")