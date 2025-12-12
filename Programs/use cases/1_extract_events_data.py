import pandas as pd
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

# Paths
DATA_DIR = os.path.join("Data", "processed")
OUTPUT_DIR = "Data/processed/UseCaseData"

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
# 🛠️ HELPER FUNCTIONS
# ==========================================

def find_row_for_date(lead_time, target_date):
    """Searches test, val, and train CSVs for the specific date."""
    folder = os.path.join(DATA_DIR, f"L{lead_time}d")

    if not os.path.exists(folder):
        print(f"      [DEBUG] Folder not found: {folder}")
        return None, None

    # Search order: Test -> Val -> Train
    files_to_check = ["test.csv", "val.csv", "train.csv"]

    for filename in files_to_check:
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue

        try:
            df = pd.read_csv(path)

            # Standardize date to string YYYY-MM-DD to match target
            if 'date' in df.columns:
                df['date_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

                row = df[df['date_str'] == target_date]
                if not row.empty:
                    # Return the row (Series) and the filename it was found in
                    return row.iloc[0], filename
        except Exception as e:
            print(f"      [DEBUG] Error reading {filename}: {e}")

    return None, None


# ==========================================
# 🚀 EXECUTION
# ==========================================
print("Phase 1: Extracting Event Data...\n")

for date, desc in TARGET_EVENTS.items():
    print(f"📅 Processing {date} ({desc})...")
    collected_rows = []

    for dt in [1, 2, 3]:
        row, source = find_row_for_date(dt, date)

        if row is not None:
            row_dict = row.to_dict()
            # Clean up temporary column
            if 'date_str' in row_dict: del row_dict['date_str']

            # Add metadata so the next script knows which model to use
            row_dict['lead_time_days'] = dt
            row_dict['source_file'] = source
            collected_rows.append(row_dict)
            print(f"   ✅ Found L{dt}d in {source}")
        else:
            print(f"   ❌ Missing L{dt}d data for {date}")

    if collected_rows:
        df_event = pd.DataFrame(collected_rows)

        # Save to CSV
        filename = f"{date}_{desc}.csv"
        save_path = os.path.join(OUTPUT_DIR, filename)

        # Reorder columns: put lead_time and date first
        cols = ['lead_time_days', 'date'] + [c for c in df_event.columns if c not in ['lead_time_days', 'date']]
        df_event = df_event[cols]

        df_event.to_csv(save_path, index=False)
        print(f"   💾 Saved to: {save_path}\n")
    else:
        print(f"   ⚠️ No data found for {date}. Skipping file creation.\n")

print("✅ Extraction Complete.")