"""
Example 3: Comparing different lead times
"""

from level_prediction import FloodPredictor
import pandas as pd

# Load data
data = pd.read_csv('path/to/your/data.csv')

# Compare 1, 2, and 3-day forecasts
results = {}

for lead_time in [1, 2, 3]:
    predictor = FloodPredictor(lead_time_days=lead_time, verbose=False)
    result = predictor.predict_from_raw_data(data)
    results[lead_time] = result

# Print comparison
print("\nFORECAST COMPARISON")
print("="*60)
print(f"{'Lead Time':<15} {'Forecast (ft)':<20} {'Risk Level':<15}")
print("-"*60)

for lead_time in sorted(results.keys()):
    fc = results[lead_time]['forecast']['median']
    risk = results[lead_time]['flood_risk']['risk_level']
    print(f"{lead_time:>2}-day{'':<10} {fc:>8.2f}{'':<11} {risk:<15}")

print("="*60)
