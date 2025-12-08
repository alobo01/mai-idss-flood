"""
Full Pipeline Test
1. Fetch latest 30 days from APIs
2. Generate 1-day and 2-day predictions
3. Display results and save outputs
"""

import pandas as pd
import json
from datetime import datetime
from data_fetcher import DataFetcher
from inference_api import FloodPredictorV2

print("="*70)
print("FULL PIPELINE TEST - LIVE DATA PREDICTION")
print("="*70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# =============================================================================
# STEP 1: FETCH LIVE DATA
# =============================================================================

print("\n" + "="*70)
print("STEP 1: FETCHING LIVE DATA FROM APIS")
print("="*70)

fetcher = DataFetcher()
fetcher.visualize_stations()

print("\nFetching data...")
raw_data = fetcher.fetch_last_30_days()

# Save raw data
output_file = "Data/live_data_latest.csv"
raw_data.to_csv(output_file, index=False)
print(f"\n💾 Raw data saved to: {output_file}")

# Display sample
print("\n📊 Sample of fetched data (last 5 days):")
print(raw_data[['date', 'target_level_max', 'hermann_level', 'grafton_level', 
                'daily_precip', 'daily_temp_avg']].tail(5).to_string(index=False))

# =============================================================================
# STEP 2: GENERATE 1-DAY PREDICTION
# =============================================================================

print("\n" + "="*70)
print("STEP 2: GENERATING 1-DAY FORECAST")
print("="*70)

try:
    predictor_1d = FloodPredictorV2(lead_time_days=1)
    result_1d = predictor_1d.predict_from_raw_data(raw_data)
    
    print("\n✅ 1-DAY PREDICTION COMPLETE")
    print("-"*70)
    
    if result_1d['current_conditions']:
        print("\n📍 Current Conditions:")
        print(f"   Date: {result_1d['current_conditions']['date']}")
        print(f"   St. Louis:  {result_1d['current_conditions']['current_level_st_louis']} ft")
        print(f"   Hermann:    {result_1d['current_conditions']['current_level_hermann']} ft")
        print(f"   Grafton:    {result_1d['current_conditions']['current_level_grafton']} ft")
        print(f"   Precip (7d): {result_1d['current_conditions']['recent_precip_7d']} mm")
    
    print(f"\n📊 1-Day Forecast: {result_1d['forecast']['median']} ft")
    print(f"   - XGBoost:  {result_1d['forecast']['xgboost']} ft")
    print(f"   - Bayesian: {result_1d['forecast']['bayesian']} ft")
    print(f"   - LSTM:     {result_1d['forecast']['lstm']} ft")
    
    print(f"\n📊 80% Conformal Prediction Interval:")
    print(f"   Lower:  {result_1d['conformal_interval_80pct']['lower']} ft")
    print(f"   Median: {result_1d['conformal_interval_80pct']['median']} ft")
    print(f"   Upper:  {result_1d['conformal_interval_80pct']['upper']} ft")
    print(f"   Width:  {result_1d['conformal_interval_80pct']['width']} ft")
    
    print(f"\n{result_1d['flood_risk']['risk_indicator']} Flood Risk (threshold: {result_1d['flood_risk']['threshold_ft']} ft):")
    print(f"   Probability: {result_1d['flood_risk']['probability']*100:.1f}%")
    print(f"   Risk Level:  {result_1d['flood_risk']['risk_level']}")
    
    # Save prediction
    with open('Results/prediction_1day_live.json', 'w') as f:
        json.dump(result_1d, f, indent=2)
    print(f"\n💾 Saved to: Results/prediction_1day_live.json")
    
except Exception as e:
    print(f"\n❌ ERROR in 1-day prediction: {e}")
    result_1d = None

# =============================================================================
# STEP 3: GENERATE 2-DAY PREDICTION
# =============================================================================

print("\n" + "="*70)
print("STEP 3: GENERATING 2-DAY FORECAST")
print("="*70)

try:
    predictor_2d = FloodPredictorV2(lead_time_days=2)
    result_2d = predictor_2d.predict_from_raw_data(raw_data)
    
    print("\n✅ 2-DAY PREDICTION COMPLETE")
    print("-"*70)
    
    print(f"\n📊 2-Day Forecast: {result_2d['forecast']['median']} ft")
    print(f"   - XGBoost:  {result_2d['forecast']['xgboost']} ft")
    print(f"   - Bayesian: {result_2d['forecast']['bayesian']} ft")
    print(f"   - LSTM:     {result_2d['forecast']['lstm']} ft")
    
    print(f"\n📊 80% Conformal Prediction Interval:")
    print(f"   Lower:  {result_2d['conformal_interval_80pct']['lower']} ft")
    print(f"   Median: {result_2d['conformal_interval_80pct']['median']} ft")
    print(f"   Upper:  {result_2d['conformal_interval_80pct']['upper']} ft")
    print(f"   Width:  {result_2d['conformal_interval_80pct']['width']} ft")
    
    print(f"\n{result_2d['flood_risk']['risk_indicator']} Flood Risk (threshold: {result_2d['flood_risk']['threshold_ft']} ft):")
    print(f"   Probability: {result_2d['flood_risk']['probability']*100:.1f}%")
    print(f"   Risk Level:  {result_2d['flood_risk']['risk_level']}")
    
    # Save prediction
    with open('Results/prediction_2day_live.json', 'w') as f:
        json.dump(result_2d, f, indent=2)
    print(f"\n💾 Saved to: Results/prediction_2day_live.json")
    
except Exception as e:
    print(f"\n❌ ERROR in 2-day prediction: {e}")
    result_2d = None

# =============================================================================
# STEP 4: COMPARISON SUMMARY
# =============================================================================

if result_1d and result_2d:
    print("\n" + "="*70)
    print("COMPARISON: 1-DAY vs 2-DAY FORECAST")
    print("="*70)
    
    comparison = pd.DataFrame({
        'Metric': [
            'Forecast (Median)',
            'Lower Bound (80%)',
            'Upper Bound (80%)',
            'Interval Width',
            'Flood Probability',
            'Risk Level'
        ],
        '1-Day': [
            f"{result_1d['forecast']['median']} ft",
            f"{result_1d['conformal_interval_80pct']['lower']} ft",
            f"{result_1d['conformal_interval_80pct']['upper']} ft",
            f"{result_1d['conformal_interval_80pct']['width']} ft",
            f"{result_1d['flood_risk']['probability']*100:.1f}%",
            result_1d['flood_risk']['risk_level']
        ],
        '2-Day': [
            f"{result_2d['forecast']['median']} ft",
            f"{result_2d['conformal_interval_80pct']['lower']} ft",
            f"{result_2d['conformal_interval_80pct']['upper']} ft",
            f"{result_2d['conformal_interval_80pct']['width']} ft",
            f"{result_2d['flood_risk']['probability']*100:.1f}%",
            result_2d['flood_risk']['risk_level']
        ]
    })
    
    print("\n" + comparison.to_string(index=False))
    
    # Calculate degradation
    print("\n📉 Forecast Degradation (1-day → 2-day):")
    
    # Median change
    median_change = result_2d['forecast']['median'] - result_1d['forecast']['median']
    print(f"   Forecast shift: {median_change:+.2f} ft")
    
    # Uncertainty increase
    width_1d = result_1d['conformal_interval_80pct']['width']
    width_2d = result_2d['conformal_interval_80pct']['width']
    uncertainty_increase = ((width_2d - width_1d) / width_1d) * 100
    print(f"   Uncertainty increase: {uncertainty_increase:+.1f}%")
    
    # Probability change
    prob_change = result_2d['flood_risk']['probability'] - result_1d['flood_risk']['probability']
    print(f"   Flood probability change: {prob_change*100:+.1f} percentage points")

# =============================================================================
# STEP 5: FINAL SUMMARY
# =============================================================================

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

print("\n📁 Output Files:")
print(f"   Raw data:       Data/live_data_latest.csv")
if result_1d:
    print(f"   1-day forecast: Results/prediction_1day_live.json")
if result_2d:
    print(f"   2-day forecast: Results/prediction_2day_live.json")

print("\n🎯 Next Steps:")
print("   1. Inspect Data/live_data_latest.csv to verify data quality")
print("   2. Review JSON files for detailed prediction outputs")
print("   3. Compare predictions with actual river levels tomorrow/day after")

print("\n" + "="*70)