"""Bootstraps the static data phase by running exploratory notebooks and the
daily/hourly processors to refresh `Data/processed/` artifacts. Use it after
ingesting new raw files so downstream modeling scripts start from consistent
inputs."""

import subprocess
import sys
import os
import time

print("=" * 70)
print("STARTING STATIC DATA PIPELINE (Preprocess & Explore)")
print("=" * 70)


scripts = [
    # 1. Generate Visualization Reports
    "Programs/01_explore.py",
    "Programs/01b_weather_features.py",
    
    # 2. Process Daily Data (Creates Data/processed/daily_flood_dataset.csv)
    "Programs/02_downsample_daily.py",

    # 3. Process Hourly Data (Creates Data/processed/hourly_flood_dataset.csv)
    "Programs/03_interpolate_hourly.py",
]

start_time = time.time()

for script in scripts:
    print(f"\n▶ Running: {script}")
    if not os.path.exists(script):
        print(f"❌ Error: Script not found: {script}")
        sys.exit(1)

    try:
        subprocess.run(f"python {script}", shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"❌ Pipeline failed at {script}")
        sys.exit(1)

print("\n" + "=" * 70)
print(f"✅ INITIALIZATION COMPLETE ({time.time() - start_time:.1f}s)")
print("   Golden Datasets created in Data/processed/")
print("=" * 70)