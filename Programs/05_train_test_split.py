import pandas as pd
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
args = parser.parse_args()

LEAD_TIME = args.days
INPUT_FILE = f"Data/processed/dataset_L{LEAD_TIME}d.csv"
OUTPUT_DIR = f"Data/processed/L{LEAD_TIME}d"

print("=" * 70)
print(f"STEP 05: SPLITTING DATA (L{LEAD_TIME}d)")
print("=" * 70)

if not os.path.exists(INPUT_FILE):
    print(f"❌ Error: {INPUT_FILE} not found. Run Step 04 first.")
    exit(1)

df = pd.read_csv(INPUT_FILE)
df['date'] = pd.to_datetime(df['date'])

# Chronological Split (Preserving 2019 flood for Validation, 2023+ for Test)
SPLIT_VAL = '2019-01-01'
SPLIT_TEST = '2023-01-01'

train = df[df['date'] < SPLIT_VAL]
val = df[(df['date'] >= SPLIT_VAL) & (df['date'] < SPLIT_TEST)]
test = df[df['date'] >= SPLIT_TEST]

os.makedirs(OUTPUT_DIR, exist_ok=True)
train.to_csv(f"{OUTPUT_DIR}/train.csv", index=False)
val.to_csv(f"{OUTPUT_DIR}/val.csv", index=False)
test.to_csv(f"{OUTPUT_DIR}/test.csv", index=False)

print(f"  ✓ Saved splits to {OUTPUT_DIR}/")
print(f"    Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")