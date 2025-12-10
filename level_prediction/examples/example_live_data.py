"""
Example 1: Basic usage with live data
"""

from level_prediction import FloodPredictor

# Initialize predictor for 1-day forecast
predictor = FloodPredictor(lead_time_days=1, verbose=True)

# Fetch live data and generate prediction
result = predictor.predict_live()

# Print results
print("\n" + "="*80)
print("PREDICTION RESULT")
print("="*80)

print(f"\n📅 Forecast Date: {result['timestamp']}")
print(f"🔮 Lead Time: {result['lead_time_days']} day(s)")

if result['current_conditions']:
    print("\n📊 Current Conditions:")
    cond = result['current_conditions']
    print(f"  St. Louis Level: {cond['current_level_st_louis']:.2f} ft")
    print(f"  Hermann Level: {cond['current_level_hermann']:.2f} ft")
    print(f"  Grafton Level: {cond['current_level_grafton']:.2f} ft")

print("\n🌊 Water Level Forecast:")
fc = result['forecast']
print(f"  Ensemble Median: {fc['median']:.2f} ft")
print(f"    - XGBoost:  {fc['xgboost']:.2f} ft")
print(f"    - Bayesian: {fc['bayesian']:.2f} ft")
print(f"    - LSTM:     {fc['lstm']:.2f} ft")

print("\n📈 Prediction Interval (80%):")
pi = result['prediction_interval_80pct']
print(f"  {pi['lower']:.2f} - {pi['upper']:.2f} ft (width: {pi['width']:.2f} ft)")

print("\n🎯 Conformal Interval (80%):")
ci = result['conformal_interval_80pct']
print(f"  {ci['lower']:.2f} - {ci['upper']:.2f} ft (median: {ci['median']:.2f} ft)")

print("\n⚠️ Flood Risk Assessment:")
risk = result['flood_risk']
print(f"  {risk['risk_indicator']} Risk Level: {risk['risk_level']}")
print(f"  Flood Probability: {risk['probability']:.1%}")
print(f"  Threshold: {risk['threshold_ft']:.1f} ft")

print("\n" + "="*80)
