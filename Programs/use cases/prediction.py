import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
import os

# --- Configuration ---
TARGET_DATES = [
    "2019-06-08",  # Highest Flood
    "2019-03-31",  # Intermediate (Major)
    "2020-04-11",  # Intermediate (Minor)
    "2023-09-02"  # Lowest Flood
]
LEAD_TIMES = [1, 2, 3]
FLOOD_THRESHOLD = 30.0

# Define paths relative to the project root (assuming script is in root or adjusted below)
# IF your Results/Data folders are in the main project folder, leave these relative.
RESULTS_DIR = "Results"
DATA_DIR = "Data/processed"


# Custom Quantile Loss
def quantile_loss(q, y_true, y_pred):
    return tf.reduce_mean(tf.maximum(q * (y_true - y_pred), (q - 1) * (y_true - y_pred)))


def prepare_features(df_raw, required_features):
    """Calculates rolling features and maps to model input."""
    df = df_raw.copy()

    # A. Calculate Rolling Features
    df['precip_7d'] = df['daily_precip'].rolling(7).sum()
    df['precip_14d'] = df['daily_precip'].rolling(14).sum()
    df['precip_30d'] = df['daily_precip'].rolling(30).sum()

    # Constant fallback or calculated if you have soil data
    df['soil_deep_30d'] = 0.5

    for w in [3, 7, 14]:
        if f'hermann_level' in df.columns:
            df[f'hermann_ma{w}d'] = df['hermann_level'].rolling(w).mean()
        if f'grafton_level' in df.columns:
            df[f'grafton_ma{w}d'] = df['grafton_level'].rolling(w).mean()

    df = df.ffill().bfill()
    today = df.iloc[-1]

    input_data = {}
    for feat in required_features:
        # 1. Direct Lags
        if 'hermann_lag' in feat:
            input_data[feat] = today.get('hermann_level', 0)
        elif 'grafton_lag' in feat:
            input_data[feat] = today.get('grafton_level', 0)
        elif 'target_lag' in feat:
            input_data[feat] = today.get('target_level_max', 0)

        # 2. Weather
        elif 'precip_7d' in feat:
            input_data[feat] = today.get('precip_7d', 0)
        elif 'precip_14d' in feat:
            input_data[feat] = today.get('precip_14d', 0)
        elif 'precip_30d' in feat:
            input_data[feat] = today.get('precip_30d', 0)
        elif 'daily_precip' in feat:
            input_data[feat] = today.get('daily_precip', 0)
        elif 'soil_deep' in feat:
            input_data[feat] = 0.5

        # 3. Rolling Stats
        elif 'hermann_ma' in feat:
            if '3d' in feat:
                input_data[feat] = today.get('hermann_ma3d', 0)
            elif '7d' in feat:
                input_data[feat] = today.get('hermann_ma7d', 0)
            elif '14d' in feat:
                input_data[feat] = today.get('hermann_ma14d', 0)
        elif 'grafton_ma' in feat:
            if '3d' in feat:
                input_data[feat] = today.get('grafton_ma3d', 0)
            elif '7d' in feat:
                input_data[feat] = today.get('grafton_ma7d', 0)
            elif '14d' in feat:
                input_data[feat] = today.get('grafton_ma14d', 0)
        else:
            input_data[feat] = 0.0

    return pd.DataFrame([input_data])


# --- 2. Load Models ---
MODELS = {}
SCALERS = {}
FEATURES = {}

# Get directory of THIS script to find the CSV files
script_dir = os.path.dirname(os.path.abspath(__file__))

print("⏳ Loading Models...")

for dt in LEAD_TIMES:
    try:
        path = f"{RESULTS_DIR}/L{dt}d"
        model_path = f"{path}/models/lstm_q90.h5"

        if not os.path.exists(model_path):
            print(f"  ⚠️ Model file not found: {model_path}")
            continue

        # Load Model
        m = load_model(model_path, custom_objects={'<lambda>': lambda y, p: quantile_loss(0.90, y, p)})

        # Load Scalers
        sx = joblib.load(f"{path}/models/lstm_scaler_x.pkl")
        sy = joblib.load(f"{path}/models/lstm_scaler_y.pkl")

        # Load Feature List from Training Data Header
        train_csv_path = f"{DATA_DIR}/L{dt}d/train.csv"
        if os.path.exists(train_csv_path):
            train_cols = pd.read_csv(train_csv_path, nrows=0).columns.tolist()
            excl = ['date', 'time', 'target_level_max', 'target_level_mean',
                    'target_level_min', 'target_level_std', 'target_level',
                    'is_flood', 'is_major_flood']
            feats = [c for c in train_cols if c not in excl]

            MODELS[dt] = m
            SCALERS[dt] = (sx, sy)
            FEATURES[dt] = feats
            print(f"  ✅ Loaded L{dt}d Model")
        else:
            print(f"  ❌ Error: Could not find train.csv at {train_csv_path} to determine features.")

    except Exception as e:
        print(f"  ❌ Error loading L{dt}d: {e}")

# --- 3. Evaluate Historical Events ---
print("\n" + "=" * 60)
print("🌊 HISTORICAL EVENT RE-FORECAST")
print("=" * 60)

for target_date in TARGET_DATES:
    # Build path to the CSV file in the SAME folder as this script
    filename = f"prediction_data_{target_date}.csv"
    full_path = os.path.join(script_dir, filename)

    if not os.path.exists(full_path):
        print(f"\n⚠️ File not found: {filename}")
        print(f"   (Looked in: {script_dir})")
        continue

    # Load Data
    df = pd.read_csv(full_path)
    df['date'] = pd.to_datetime(df['date'])

    # Get actual event level (last row)
    actual_event_level = df.iloc[-1]['target_level_max']

    # Remove the event day itself to simulate "Live" prediction
    input_df = df.iloc[:-1].reset_index(drop=True)

    print(f"\n📅 Event Date: {target_date}")
    print(f"   Actual Water Level: {actual_event_level:.2f} ft")

    # Ensure inputs are valid
    last_input_date = input_df.iloc[-1]['date']
    print(f"   (Input Data Ends: {last_input_date.date()})")
    print("-" * 40)

    for dt in LEAD_TIMES:
        if dt not in MODELS: continue

        # Prepare Features
        feats_list = FEATURES[dt]
        X = prepare_features(input_df, feats_list)

        # Scale & Predict
        try:
            scaler_x, scaler_y = SCALERS[dt]

            # Ensure feature order matches training
            X = X[feats_list]

            X_s = scaler_x.transform(X).reshape((1, 1, len(feats_list)))

            # Predict
            pred_scaled = MODELS[dt].predict(X_s, verbose=0)
            pred_ft = scaler_y.inverse_transform(pred_scaled)[0][0]

            # Logic
            label = f"T+{dt}d Forecast"

            # Simple Emoji Status
            if pred_ft >= FLOOD_THRESHOLD:
                status = "⚠️ FLOOD PREDICTED"
            else:
                status = "✅ Safe"

            print(f"   {label}: {pred_ft:.2f} ft  [{status}]")

        except Exception as e:
            print(f"   L{dt}d Prediction Error: {e}")