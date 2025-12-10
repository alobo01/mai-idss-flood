#!/usr/bin/env python
"""
Quick test script to verify the level_prediction package is properly installed and functional
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from level_prediction import FloodPredictor, DataFetcher, FeatureEngineer, get_latest_data
        print("  ✓ All main classes imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        from level_prediction import config
        
        # Check key config values
        assert config.FLOOD_THRESHOLD_FT == 30.0, "Invalid flood threshold"
        assert config.DEFAULT_LEAD_TIME == 1, "Invalid default lead time"
        assert len(config.STATIONS) == 3, "Invalid number of stations"
        assert len(config.AVAILABLE_LEAD_TIMES) == 3, "Invalid lead times"
        
        print(f"  ✓ Configuration loaded")
        print(f"    - Flood threshold: {config.FLOOD_THRESHOLD_FT} ft")
        print(f"    - Available lead times: {config.AVAILABLE_LEAD_TIMES}")
        print(f"    - Stations: {len(config.STATIONS)}")
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False

def test_model_paths():
    """Test that model directories exist"""
    print("\nTesting model paths...")
    try:
        from level_prediction import config
        
        for lead_time in config.AVAILABLE_LEAD_TIMES:
            model_path = config.get_model_path(lead_time)
            exists = model_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} L{lead_time}d models: {model_path}")
            
            if not exists:
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Model path test failed: {e}")
        return False

def test_model_files():
    """Test that all required model files exist"""
    print("\nTesting model files...")
    try:
        from level_prediction import config
        
        required_files = [
            'xgb_q10.json', 'xgb_q50.json', 'xgb_q90.json',
            'bayes_model.pkl', 'bayes_scaler.pkl',
            'lstm_q10.h5', 'lstm_q50.h5', 'lstm_q90.h5',
            'lstm_scaler_x.pkl', 'lstm_scaler_y.pkl',
            'calibration_info.pkl',
        ]
        
        for lead_time in [1]:  # Just check L1d
            model_path = config.get_model_path(lead_time)
            missing = []
            
            for file in required_files:
                if not (model_path / file).exists():
                    missing.append(file)
            
            if missing:
                print(f"  ✗ L{lead_time}d: Missing files: {missing}")
                return False
            else:
                print(f"  ✓ L{lead_time}d: All required files present")
        
        return True
    except Exception as e:
        print(f"  ✗ Model file test failed: {e}")
        return False

def test_instantiation():
    """Test that predictor can be instantiated"""
    print("\nTesting predictor instantiation...")
    try:
        from level_prediction import FloodPredictor
        
        # This will attempt to load models
        predictor = FloodPredictor(lead_time_days=1, verbose=False)
        print(f"  ✓ FloodPredictor instantiated successfully")
        print(f"    - Lead time: {predictor.lead_time} day(s)")
        print(f"    - Model directory: {predictor.model_dir}")
        print(f"    - Conformal correction: {predictor.conformal_correction:.2f} ft")
        return True
    except Exception as e:
        print(f"  ✗ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_feature_engineer():
    """Test feature engineer initialization"""
    print("\nTesting feature engineer...")
    try:
        from level_prediction import FeatureEngineer
        
        engineer = FeatureEngineer(lead_time_days=1)
        print(f"  ✓ FeatureEngineer instantiated")
        print(f"    - Features: {len(engineer.feature_order)}")
        return True
    except Exception as e:
        print(f"  ✗ FeatureEngineer test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("LEVEL PREDICTION PACKAGE TEST SUITE")
    print("="*70)
    
    tests = [
        test_imports,
        test_config,
        test_model_paths,
        test_model_files,
        test_feature_engineer,
        test_instantiation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED - Package is ready to use!")
        print("\nNext steps:")
        print("1. Install the package:")
        print("   pip install -e /path/to/level_prediction")
        print("\n2. Use it in your code:")
        print("   from level_prediction import FloodPredictor")
        print("   predictor = FloodPredictor(lead_time_days=1)")
        print("   result = predictor.predict_live()")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Please check the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
