"""
Test Script for Flood Prediction Inference API
Tests the API with real trained models and actual test data
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from inference_api import FloodPredictorV2

def print_header(text):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_result(result):
    """Pretty print prediction results"""
    print_header("PREDICTION RESULTS")
    
    print(f"\n📅 Timestamp: {result['timestamp']}")
    print(f"🔮 Lead Time: {result['lead_time_days']} day(s)")
    
    if result['current_conditions']:
        print_header("CURRENT CONDITIONS")
        cond = result['current_conditions']
        print(f"  Date: {cond['date']}")
        print(f"  St. Louis Level: {cond['current_level_st_louis']:.2f} ft")
        print(f"  Hermann Level: {cond['current_level_hermann']:.2f} ft")
        print(f"  Grafton Level: {cond['current_level_grafton']:.2f} ft")
        print(f"  Recent Precipitation (7d): {cond['recent_precip_7d']:.2f} in")
    
    print_header("FORECAST")
    fc = result['forecast']
    print(f"  📊 Ensemble Median: {fc['median']:.2f} ft")
    print(f"     XGBoost:        {fc['xgboost']:.2f} ft")
    print(f"     Bayesian:       {fc['bayesian']:.2f} ft")
    print(f"     LSTM:           {fc['lstm']:.2f} ft")
    
    print_header("PREDICTION INTERVALS (80%)")
    pi = result['prediction_interval_80pct']
    print(f"  Lower: {pi['lower']:.2f} ft")
    print(f"  Upper: {pi['upper']:.2f} ft")
    print(f"  Width: {pi['width']:.2f} ft")
    
    print_header("CONFORMAL INTERVALS (80%)")
    ci = result['conformal_interval_80pct']
    print(f"  Lower:  {ci['lower']:.2f} ft")
    print(f"  Median: {ci['median']:.2f} ft")
    print(f"  Upper:  {ci['upper']:.2f} ft")
    print(f"  Width:  {ci['width']:.2f} ft")
    
    print_header("FLOOD RISK ASSESSMENT")
    risk = result['flood_risk']
    print(f"  {risk['risk_indicator']} Risk Level: {risk['risk_level']}")
    print(f"  Flood Probability: {risk['probability']:.1%}")
    print(f"  Threshold: {risk['threshold_ft']:.1f} ft")
    
    print("\n" + "="*80 + "\n")

def test_single_prediction(lead_time=1):
    """Test a single prediction with real models"""
    print_header(f"TEST 1: Single Prediction ({lead_time}-day forecast)")
    
    # Load test data
    test_data = pd.read_csv("/home/alono/MAI/IDSS/Data/processed/daily_test.csv")
    print(f"✓ Loaded test data: {len(test_data)} samples")
    
    # Initialize predictor
    predictor = FloodPredictorV2(lead_time_days=lead_time)
    
    # Get a sample from the middle of test set
    sample_idx = len(test_data) // 2
    print(f"\nTesting on sample index {sample_idx} (mid-test set)")
    
    # Create historical window (last 30 days before prediction point)
    if sample_idx < 30:
        print(f"⚠️  Sample too early, using first 30 days")
        sample_idx = 30
    
    historical_data = test_data.iloc[sample_idx-30:sample_idx].copy()
    
    # Make prediction
    print("\n🔄 Generating prediction...")
    result = predictor.predict_from_raw_data(historical_data)
    
    # Print results
    print_result(result)
    
    # Get actual value if available
    if sample_idx < len(test_data):
        actual_value = test_data.iloc[sample_idx]['target_level_max']
        predicted_value = result['forecast']['median']
        error = predicted_value - actual_value
        
        print(f"📊 Validation:")
        print(f"   Actual Value: {actual_value:.2f} ft")
        print(f"   Predicted:    {predicted_value:.2f} ft")
        print(f"   Error:        {error:.2f} ft ({error/actual_value*100:.1f}%)")
        
        # Check if actual is in prediction interval
        in_pi = result['prediction_interval_80pct']['lower'] <= actual_value <= result['prediction_interval_80pct']['upper']
        in_ci = result['conformal_interval_80pct']['lower'] <= actual_value <= result['conformal_interval_80pct']['upper']
        
        print(f"   In Prediction Interval: {'✓' if in_pi else '✗'}")
        print(f"   In Conformal Interval:  {'✓' if in_ci else '✗'}")
    
    return result

def test_multiple_predictions(lead_time=1, n_samples=5):
    """Test multiple predictions and compute metrics"""
    print_header(f"TEST 2: Multiple Predictions ({n_samples} samples, {lead_time}-day forecast)")
    
    # Load test data
    test_data = pd.read_csv("/home/alono/MAI/IDSS/Data/processed/daily_test.csv")
    
    # Initialize predictor
    predictor = FloodPredictorV2(lead_time_days=lead_time)
    
    # Select evenly spaced samples
    indices = np.linspace(50, len(test_data)-10, n_samples, dtype=int)
    
    results = []
    errors = []
    in_pi_count = 0
    in_ci_count = 0
    
    print(f"\nProcessing {n_samples} predictions...\n")
    
    for i, idx in enumerate(indices):
        print(f"Sample {i+1}/{n_samples} (index {idx})...", end=" ")
        
        # Get historical data
        historical_data = test_data.iloc[idx-30:idx].copy()
        
        # Predict
        result = predictor.predict_from_raw_data(historical_data)
        
        # Get actual
        actual_value = test_data.iloc[idx]['target_level_max']
        predicted_value = result['forecast']['median']
        error = predicted_value - actual_value
        
        errors.append(error)
        
        # Check coverage
        in_pi = result['prediction_interval_80pct']['lower'] <= actual_value <= result['prediction_interval_80pct']['upper']
        in_ci = result['conformal_interval_80pct']['lower'] <= actual_value <= result['conformal_interval_80pct']['upper']
        
        if in_pi:
            in_pi_count += 1
        if in_ci:
            in_ci_count += 1
        
        results.append({
            'index': idx,
            'actual': actual_value,
            'predicted': predicted_value,
            'error': error,
            'in_pi': in_pi,
            'in_ci': in_ci,
            'flood_prob': result['flood_risk']['probability'],
            'risk_level': result['flood_risk']['risk_level']
        })
        
        print(f"✓ Error: {error:+.2f} ft")
    
    # Compute metrics
    print_header("AGGREGATE METRICS")
    
    errors = np.array(errors)
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))
    mape = np.mean(np.abs(errors / [r['actual'] for r in results])) * 100
    
    print(f"\n📈 Error Metrics:")
    print(f"   MAE:  {mae:.3f} ft")
    print(f"   RMSE: {rmse:.3f} ft")
    print(f"   MAPE: {mape:.2f}%")
    
    pi_coverage = in_pi_count / n_samples * 100
    ci_coverage = in_ci_count / n_samples * 100
    
    print(f"\n📊 Coverage:")
    print(f"   Prediction Interval (80%): {pi_coverage:.1f}% ({in_pi_count}/{n_samples})")
    print(f"   Conformal Interval (80%):  {ci_coverage:.1f}% ({in_ci_count}/{n_samples})")
    
    # Risk level distribution
    risk_counts = {}
    for r in results:
        risk_counts[r['risk_level']] = risk_counts.get(r['risk_level'], 0) + 1
    
    print(f"\n🚨 Risk Level Distribution:")
    for level in ['LOW', 'MODERATE', 'HIGH']:
        count = risk_counts.get(level, 0)
        pct = count / n_samples * 100
        print(f"   {level:10s}: {count}/{n_samples} ({pct:.1f}%)")
    
    return results

def test_all_lead_times():
    """Test all available lead times"""
    print_header("TEST 3: All Lead Times")
    
    lead_times = [1, 2, 3]
    test_data = pd.read_csv("/home/alono/MAI/IDSS/Data/processed/daily_test.csv")
    
    # Use same sample for all lead times
    sample_idx = len(test_data) // 2
    historical_data = test_data.iloc[sample_idx-30:sample_idx].copy()
    
    results = {}
    
    for lead_time in lead_times:
        print(f"\n📅 Testing {lead_time}-day forecast...")
        
        try:
            predictor = FloodPredictorV2(lead_time_days=lead_time)
            result = predictor.predict_from_raw_data(historical_data)
            results[lead_time] = result
            print(f"   ✓ Prediction: {result['forecast']['median']:.2f} ft")
            print(f"   ✓ Risk: {result['flood_risk']['risk_level']}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            continue
    
    # Compare predictions
    if len(results) > 1:
        print_header("LEAD TIME COMPARISON")
        print("\n📊 Forecasts:")
        for lead_time in sorted(results.keys()):
            fc = results[lead_time]['forecast']['median']
            risk = results[lead_time]['flood_risk']['risk_level']
            prob = results[lead_time]['flood_risk']['probability']
            print(f"   {lead_time}-day: {fc:.2f} ft | {risk} ({prob:.1%})")
    
    return results

def test_edge_cases(lead_time=1):
    """Test edge cases and error handling"""
    print_header("TEST 4: Edge Cases")
    
    test_data = pd.read_csv("/home/alono/MAI/IDSS/Data/processed/daily_test.csv")
    predictor = FloodPredictorV2(lead_time_days=lead_time)
    
    print("\n1️⃣  Testing with minimum data (30 days)...")
    try:
        minimal_data = test_data.iloc[:30].copy()
        result = predictor.predict_from_raw_data(minimal_data)
        print(f"   ✓ Success: {result['forecast']['median']:.2f} ft")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n2️⃣  Testing with high water level period...")
    try:
        # Find period with high water
        high_water_idx = test_data['target_level_max'].idxmax()
        if high_water_idx >= 30:
            high_water_data = test_data.iloc[high_water_idx-30:high_water_idx].copy()
            result = predictor.predict_from_raw_data(high_water_data)
            print(f"   ✓ Prediction: {result['forecast']['median']:.2f} ft")
            print(f"   ✓ Risk: {result['flood_risk']['risk_level']} ({result['flood_risk']['probability']:.1%})")
        else:
            print("   ⚠️  High water too early in dataset")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n3️⃣  Testing with low water level period...")
    try:
        # Find period with low water
        low_water_idx = test_data['target_level_max'].idxmin()
        if low_water_idx >= 30:
            low_water_data = test_data.iloc[low_water_idx-30:low_water_idx].copy()
            result = predictor.predict_from_raw_data(low_water_data)
            print(f"   ✓ Prediction: {result['forecast']['median']:.2f} ft")
            print(f"   ✓ Risk: {result['flood_risk']['risk_level']} ({result['flood_risk']['probability']:.1%})")
        else:
            print("   ⚠️  Low water too early in dataset")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

def save_test_results(results, filename="test_results.json"):
    """Save test results to JSON file"""
    output_path = f"/home/alono/MAI/IDSS/Programs/{filename}"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {output_path}")

def main():
    """Run all tests"""
    print_header("INFERENCE API TEST SUITE")
    print(f"Testing with REAL trained models")
    print(f"Test Data: /home/alono/MAI/IDSS/Data/processed/daily_test.csv")
    print(f"Models: /home/alono/MAI/IDSS/Results/L[1-3]d/models")
    
    try:
        # Test 1: Single prediction
        result_single = test_single_prediction(lead_time=1)
        
        # Test 2: Multiple predictions with metrics
        results_multiple = test_multiple_predictions(lead_time=1, n_samples=10)
        
        # Test 3: All lead times
        results_all_lead = test_all_lead_times()
        
        # Test 4: Edge cases
        test_edge_cases(lead_time=1)
        
        # Save results
        all_results = {
            'single_prediction': result_single,
            'multiple_predictions': results_multiple,
            'all_lead_times': {k: v for k, v in results_all_lead.items()},
            'test_timestamp': datetime.now().isoformat()
        }
        save_test_results(all_results)
        
        print_header("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print_header("❌ TEST FAILED")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
