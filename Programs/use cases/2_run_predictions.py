import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
import os

# Suppress TensorFlow info messages (keeps output clean)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
RESULTS_DIR = "Results"
DATA_DIR = os.path.join("Data", "processed")
EVENT_DIR = "Data/processed/UseCaseData"


# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def quantile_loss(q, y_true, y_pred):
    return tf.reduce_mean(tf.maximum(q * (y_true - y_pred), (q - 1) * (y_true - y_pred)))


def get_feature_columns(lead_time):
    path = os.path.join(DATA_DIR, f"L{lead_time}d", "train.csv")
    if not os.path.exists(path): return []
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    exclude = ['date', 'time', 'target_level_max', 'target_level_mean',
               'target_level_min', 'target_level_std', 'target_level',
               'is_flood', 'is_major_flood']
    return [c for c in cols if c not in exclude]


# ==========================================
# 🚀 1. LOAD MODELS ONCE (The Fix)
# ==========================================
print("⏳ Loading all models into memory...")
SYSTEMS = {}  # Dictionary to store (model, scaler_x, scaler_y, features)

for dt in [1, 2, 3]:
    try:
        # Paths
        model_path = os.path.join(RESULTS_DIR, f"L{dt}d", "models", "lstm_q90.h5")
        sx_path = os.path.join(RESULTS_DIR, f"L{dt}d", "models", "lstm_scaler_x.pkl")
        sy_path = os.path.join(RESULTS_DIR, f"L{dt}d", "models", "lstm_scaler_y.pkl")

        if os.path.exists(model_path):
            # Load components
            m = load_model(model_path, custom_objects={'<lambda>': lambda y, p: quantile_loss(0.90, y, p)})
            sx = joblib.load(sx_path)
            sy = joblib.load(sy_path)
            feats = get_feature_columns(dt)

            # Save to dictionary
            SYSTEMS[dt] = (m, sx, sy, feats)
            print(f"   ✅ L{dt}d System Loaded")
        else:
            print(f"   ⚠️ L{dt}d Model missing")

    except Exception as e:
        print(f"   ❌ Error loading L{dt}d: {e}")

# ==========================================
# 🚀 2. RUN PREDICTIONS
# ==========================================
print("\nPhase 2: Running Predictions...\n")

event_files = [f for f in os.listdir(EVENT_DIR) if f.endswith(".csv")]

for filename in event_files:
    print(f"🔍 Analyzing: {filename}")
    print("-" * 40)

    file_path = os.path.join(EVENT_DIR, filename)
    df_event = pd.read_csv(file_path)

    for idx, row in df_event.iterrows():
        dt = int(row['lead_time_days'])

        if dt not in SYSTEMS:
            print(f"   ⚠️ No loaded model for L{dt}d")
            continue

        # Retrieve pre-loaded components
        model, scaler_x, scaler_y, feats = SYSTEMS[dt]

        try:
            # Prepare Input
            X_input = pd.DataFrame([row])
            for f in feats:
                if f not in X_input.columns: X_input[f] = 0.0

            X_input = X_input[feats]

            # Predict
            X_scaled = scaler_x.transform(X_input)
            X_reshaped = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))

            y_scaled = model.predict(X_reshaped, verbose=0)
            y_pred = scaler_y.inverse_transform(y_scaled)[0][0]

            # Truth
            truth = row.get('target_level_max', row.get('target_level', np.nan))

            diff = y_pred - truth
            emoji = "✅" if abs(diff) < 2.0 else "⚠️"

            print(f"   L{dt}d Prediction: {y_pred:.2f} ft  |  Truth: {truth:.2f} ft  |  Diff: {diff:+.2f} {emoji}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n")

print("✅ Analysis Complete.")