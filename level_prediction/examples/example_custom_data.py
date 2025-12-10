"""
Example 2: Using custom data
"""

import pandas as pd
from level_prediction import FloodPredictor

# Load your own data (needs 30+ days)
data = pd.read_csv('path/to/your/data.csv')

# Initialize predictor
predictor = FloodPredictor(lead_time_days=1)

# Generate prediction from your data
result = predictor.predict_from_raw_data(data)

# Extract key metrics
forecast_level = result['forecast']['median']
risk_level = result['flood_risk']['risk_level']
flood_prob = result['flood_risk']['probability']

print(f"Predicted Level: {forecast_level:.2f} ft")
print(f"Risk: {risk_level} ({flood_prob:.1%})")

# Use prediction interval for operational decision-making
pi = result['prediction_interval_80pct']
print(f"80% Prediction Interval: {pi['lower']:.2f} - {pi['upper']:.2f} ft")

# Use conformal interval for conservative estimates
ci = result['conformal_interval_80pct']
print(f"80% Conformal Interval: {ci['lower']:.2f} - {ci['upper']:.2f} ft")
