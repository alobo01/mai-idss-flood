"""
Create raw dataset for frontend (no feature engineering)
"""
import pandas as pd
import os

print("Creating raw frontend dataset...")

# FIRST: Just check what we have
data_dir = "Data/datasets"

print("\n" + "="*70)
print("INSPECTING RAW DATA FILES")
print("="*70)

files_to_check = [
    "river_target_st_louis.csv",
    "river_upstream_hermann.csv", 
    "river_upstream_grafton.csv",
]

for filename in files_to_check:
    filepath = f"{data_dir}/{filename}"
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, nrows=5)  # Just load 5 rows
        print(f"\n📄 {filename}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample row:")
        print(df.head(1))
    else:
        print(f"\n❌ {filename} - NOT FOUND")

print("\n" + "="*70)
print("CHECKING ALTERNATIVE: processed daily dataset")
print("="*70)

daily_file = "Data/processed/daily_flood_dataset.csv"
if os.path.exists(daily_file):
    df = pd.read_csv(daily_file, nrows=5)
    print(f"\n✓ Found: {daily_file}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample:")
    print(df.head())
    
    # THIS IS WHAT WE'LL USE
    print("\n" + "="*70)
    print("CREATING FRONTEND DATASET from processed daily")
    print("="*70)
    
    # Load full dataset
    df_full = pd.read_csv(daily_file)
    df_full['date'] = pd.to_datetime(df_full['date'])
    
    # Select ONLY raw columns (no lags, no MAs, no rolling windows)
    raw_columns = [
        'date',
        'target_level_max',    # St. Louis 
        'hermann_level',       # Hermann upstream
        'grafton_level',       # Grafton upstream  
        'daily_precip',        
        'daily_temp_avg',      
        'daily_humidity',      
        'daily_wind',          
        'soil_deep_30d',       
    ]
    
    # Only keep columns that exist
    available = [c for c in raw_columns if c in df_full.columns]
    raw_dataset = df_full[available].copy()
    
    # Sort by date
    raw_dataset = raw_dataset.sort_values('date').reset_index(drop=True)
    
    # Save
    output_file = "Data/frontend_raw_data.csv"
    raw_dataset.to_csv(output_file, index=False)
    
    print(f"\n✅ Created: {output_file}")
    print(f"   Rows: {len(raw_dataset):,}")
    print(f"   Date range: {raw_dataset['date'].min()} to {raw_dataset['date'].max()}")
    print(f"   Columns: {list(raw_dataset.columns)}")
    
    print("\nSample (last 5 days):")
    print(raw_dataset.tail())
    
else:
    print(f"\n❌ {daily_file} not found!")
    print("\nYou need to run: python Programs/02_downsample_daily.py")