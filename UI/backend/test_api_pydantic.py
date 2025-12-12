import requests
import json
import sys
from datetime import datetime

def test_prediction_endpoint():
    """Test the /predict endpoint with Pydantic validation."""
    print("🔍 Testing /predict endpoint...")

    try:
        # Test 1-day prediction
        response = requests.get("http://localhost:8003/predict?days_ahead=1", timeout=30)
        assert response.status_code == 200

        data = response.json()

        # Validate response structure
        assert "lead_time_days" in data
        assert "predictions" in data
        assert "flood_risk" in data

        # Validate predictions structure
        predictions = data["predictions"]
        assert isinstance(predictions, list)

        if predictions:
            pred = predictions[0]
            assert "date" in pred
            assert "level" in pred
            assert "probability" in pred

            # Test that probability is properly validated (0-1)
            assert 0 <= pred["probability"] <= 1

        print("✅ /predict endpoint validation passed")
        return True

    except Exception as e:
        print(f"❌ /predict endpoint test failed: {e}")
        return False

def test_zones_endpoint():
    """Test the /zones endpoint with Pydantic Zone models."""
    print("🔍 Testing /zones endpoint...")

    try:
        response = requests.get("http://localhost:8003/zones", timeout=30)
        assert response.status_code == 200

        zones = response.json()
        assert isinstance(zones, list)

        if zones:
            zone = zones[0]
            # Validate Zone model structure
            assert "zone_id" in zone
            assert "name" in zone
            assert "pf" in zone
            assert "vulnerability" in zone
            assert "is_critical_infra" in zone
            assert "hospital_count" in zone

            # Test data types
            assert isinstance(zone["pf"], (int, float))
            assert isinstance(zone["vulnerability"], (int, float))
            assert isinstance(zone["is_critical_infra"], bool)

        print("✅ /zones endpoint validation passed")
        return True

    except Exception as e:
        print(f"❌ /zones endpoint test failed: {e}")
        return False

def test_rule_based_dispatch_endpoint():
    """Test the /rule-based/dispatch endpoint with Allocation models."""
    print("🔍 Testing /rule-based/dispatch endpoint...")

    try:
        response = requests.get("http://localhost:8003/rule-based/dispatch", timeout=30)
        assert response.status_code == 200

        data = response.json()

        # Validate response structure
        assert "summary" in data
        assert "allocations" in data

        allocations = data["allocations"]
        assert isinstance(allocations, list)

        if allocations:
            allocation = allocations[0]
            # Validate Allocation model structure
            assert "zone_id" in allocation
            assert "zone_name" in allocation
            assert "impact_level" in allocation
            assert "allocation_mode" in allocation
            assert "units_allocated" in allocation

            # Test enum validation
            assert allocation["impact_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
            assert allocation["allocation_mode"] in ["FUZZY", "OPTIMISTIC", "CONSERVATIVE"]

        print("✅ /rule-based/dispatch endpoint validation passed")
        return True

    except Exception as e:
        print(f"❌ /rule-based/dispatch endpoint test failed: {e}")
        return False

def main():
    """Run all API tests."""
    print("🧪 Docker-based API Pydantic Tests")
    print("=" * 40)

    tests = [
        ("Prediction Endpoint", test_prediction_endpoint),
        ("Zones Endpoint", test_zones_endpoint),
        ("Rule-based Dispatch", test_rule_based_dispatch_endpoint),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            failed += 1

    print(f"\n📊 Test Results:")
    print(f"===============")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")

    if failed == 0:
        print("\n🎉 All API tests passed! Pydantic implementation working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
