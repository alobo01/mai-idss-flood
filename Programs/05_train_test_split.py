import pandas as pd
import argparse
import os
import matplotlib.pyplot as plt

# =============================================================================
# CONFIGURATION
# =============================================================================
parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1, help="Lead time in days")
args = parser.parse_args()

LEAD_TIME = args.days
INPUT_FILE = f"Data/processed/dataset_L{LEAD_TIME}d.csv"
OUTPUT_DIR = f"Data/processed/L{LEAD_TIME}d"

# NEW SPLIT DATES (To include 2019 Flood in Test)
# Train: Start -> 2012 (Includes 2008 flood)
# Val:   2013 -> 2018  (Includes 2013 & 2016 floods for tuning)
# Test:  2019 -> End   (Includes MAJOR 2019 flood for final exam)
SPLIT_VAL_START = '2013-01-01'
SPLIT_TEST_START = '2019-01-01'

print("=" * 70)
print(f"STEP 05: SPLITTING DATA (L{LEAD_TIME}d)")
print(f"Strategy: Heavy Flood Testing (Test Set starts {SPLIT_TEST_START})")
print("=" * 70)

if not os.path.exists(INPUT_FILE):
    print(f"❌ Error: {INPUT_FILE} not found. Run Step 04 first.")
    exit(1)

# 1. Load Data
df = pd.read_csv(INPUT_FILE)
df['date'] = pd.to_datetime(df['date'])

# 2. Apply Splits
train = df[df['date'] < SPLIT_VAL_START].copy()
val = df[(df['date'] >= SPLIT_VAL_START) & (df['date'] < SPLIT_TEST_START)].copy()
test = df[df['date'] >= SPLIT_TEST_START].copy()

# 3. Save
os.makedirs(OUTPUT_DIR, exist_ok=True)
train.to_csv(f"{OUTPUT_DIR}/train.csv", index=False)
val.to_csv(f"{OUTPUT_DIR}/val.csv", index=False)
test.to_csv(f"{OUTPUT_DIR}/test.csv", index=False)

# 4. Flood Stats Check
FLOOD_THRESHOLD = 30.0
def count_floods(data, name):
    # Check if we have the 'target_level_max' column (daily) or 'target_level' (hourly)
    col = 'target_level_max' if 'target_level_max' in data.columns else 'target_level'
    floods = (data[col] >= FLOOD_THRESHOLD).sum()
    print(f"  {name}: {len(data)} rows | {floods} Flood Days ({floods/len(data)*100:.1f}%)")

print("\nSplit Statistics:")
count_floods(train, "Train (2001-2012)")
count_floods(val,   "Val   (2013-2018)")
count_floods(test,  "Test  (2019-2025)")

print(f"\n✅ Splits saved to: {OUTPUT_DIR}/")