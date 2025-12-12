import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
import os

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================

TARGET_EVENTS = {
    "2019-06-08": "highest_flood",
    "2019-03-31": "major_flood",
    "2020-04-11": "minor_flood",
    "2023-09-02": "lowest_flood"
}

# UPDATE: Pointing to "Data/processed" as you requested
DATA_DIR = os.path.join("Data", "processed")
RESULTS_DIR = "Results"
OUTPUT_DIR = "Event_Analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================

def quantile_loss(q, y_true, y_pred):
    return tf.reduce_mean(tf.maximum(q * (y_true - y_pred), (q - 1) * (y_true - y_pred)))


def get_feature_columns(lead_time):
    # Construct path: Data/processed/L{x}d/train.csv
    path = os.path.join(DATA_DIR, f"L{lead_time}d", "train.csv")

    if not os.path.exists(path):
        print(f"   ⚠️ Warning: Could not find feature source at {path}")
        return []

    cols = pd.read_csv(path, nrows=0).columns.tolist()
    exclude = ['date', 'time', 'target_level_max', 'target_level_mean',
               'target_level_min', 'target_level_std', 'target_level',
               'is_flood', 'is_major_flood']
    return [c for c in cols if c not in exclude]


def find_row_for_date(lead_time, target_date):
    """Searches test, val, and train CSVs for the specific date."""
    folder = os.path.join(DATA_DIR, f"L{lead_time}d")

    # Debug: verify folder exists
    if not os.path.exists(folder):
        print(f"      [DEBUG] Folder not found: {folder}")
        return None, None

    files_to_check = ["test.csv", "val.csv", "train.csv"]

    for filename in files_to_check:
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue

        try:
            df = pd.read_csv(path)

            # STANDARDISATION: Ensure date is string YYYY-MM-DD
            # This handles cases where date might have time (2019-06-08 00:00:00)
            if 'date' in df.columns:
                # Convert to datetime then back to string to strip time if present
                df['date_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

                row = df[df['date_str'] == target_date]
                if not row.empty:
                    return row.iloc[0], filename
        except Exception as e:
            print(f"      [DEBUG] Error reading {filename}: {e}")

    return None, None


# ==========================================
# 🔍 DIAGNOSTIC CHECK
# ==========================================
print("--- 🔍 DIAGNOSTIC CHECK ---")
abs_data_path = os.path.abspath(DATA_DIR)
print(f"Looking for data in: {abs_data_path}")

if os.path.exists(abs_data_path):
    print("✅ Data folder exists.")
    l1d_path = os.path.join(abs_data_path, "L1d")
    if os.path.exists(l1d_path):
        print(f"✅ Found L1d folder. Contents: {os.listdir(l1d_path)}")
    else:
        print(f"❌ Could not find 'L1d' folder inside {abs_data_path}")
else:
    print(f"❌ The folder '{abs_data_path}' does not exist.")
    print("   Please check where you are running the script from.")
print("---------------------------\n")

# ==========================================
# 🚀 PHASE 1: EXTRACT & SAVE CSVs
# ==========================================
print("Phase 1: Extracting Event Data...\n")
event_files = {}

for date, desc in TARGET_EVENTS.items():
    print(f"📅 Processing {date} ({desc})...")
    collected_rows = []

    for dt in [1, 2, 3]:
        row, source = find_row_for_date(dt, date)

        if row is not None:
            row_dict = row.to_dict()
            # Clean up the temp column if it got added
            if 'date_str' in row_dict: del row_dict['date_str']

            row_dict['lead_time_days'] = dt
            row_dict['source_file'] = source
            collected_rows.append(row_dict)
            print(f"   ✅ Found L{dt}d in {source}")
        else:
            print(f"   ❌ Missing L{dt}d data for {date}")

    if collected_rows:
        df_event = pd.DataFrame(collected_rows)
        filename = f"{date}_{desc}.csv"
        save_path = os.path.join(OUTPUT_DIR, filename)

        # Reorder for readability
        cols = ['lead_time_days', 'date'] + [c for c in df_event.columns if c not in ['lead_time_days', 'date']]
        df_event = df_event[cols]

        df_event.to_csv(save_path, index=False)
        event_files[date] = save_path
        print(f"   💾 Saved to: {save_path}\n")
    else:
        print(f"   ⚠️ No data found for {date}. Skipping.\n")

# ==========================================
# 🔮 PHASE 2: PREDICTION
# ==========================================
print("=" * 60)
print("Phase 2: Running Predictions")
print("=" * 60)

for date, csv_path in event_files.items():
    desc = TARGET_EVENTS[date]
    print(f"\n🔍 Analyzing Event: {desc} ({date})")
    print("-" * 40)

    df_event = pd.read_csv(csv_path)

    for idx, row in df_event.iterrows():
        dt = int(row['lead_time_days'])

        # Construct Model Paths
        model_path = os.path.join(RESULTS_DIR, f"L{dt}d", "models", "lstm_q90.h5")
        scaler_x_path = os.path.join(RESULTS_DIR, f"L{dt}d", "models", "lstm_scaler_x.pkl")
        scaler_y_path = os.path.join(RESULTS_DIR, f"L{dt}d", "models", "lstm_scaler_y.pkl")

        if not os.path.exists(model_path):
            print(f"   ⚠️ L{dt}d Model not found at {model_path}")
            continue

        try:
            # Load Model & Scalers
            model = load_model(model_path, custom_objects={'<lambda>': lambda y, p: quantile_loss(0.90, y, p)})
            scaler_x = joblib.load(scaler_x_path)
            scaler_y = joblib.load(scaler_y_path)

            # Get Features
            feats = get_feature_columns(dt)
            if not feats: continue

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

            # Output
            diff = y_pred - truth
            emoji = "✅" if abs(diff) < 2.0 else "⚠️"
            print(f"   L{dt}d Prediction: {y_pred:.2f} ft  |  Truth: {truth:.2f} ft  |  Diff: {diff:+.2f} {emoji}")

        except Exception as e:
            print(f"   ❌ Error processing L{dt}d: {e}")

print("\n✅ Done.")