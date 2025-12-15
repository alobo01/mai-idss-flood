#!/usr/bin/env python3
"""
Live API test for Pydantic typing implementation.
Tests the actual running backend to verify Pydantic models are working correctly.
"""

import requests
import json
import sys
from datetime import datetime

def test_prediction_endpoint():
    """Test the /predict endpoint with Pydantic validation."""
    print("🔍 Testing /predict endpoint...")

    try:
        # Test 1-day prediction
        response = requests.get("http://localhost:8003/predict?days_ahead=1")
        assert response.status_code == 200

        data = response.json()

        # Validate response structure
        assert "lead_time_days" in data
        assert "predictions" in data
        assert "flood_risk" in data
        assert "current_conditions" in data
        assert "forecast" in data

        # Validate predictions structure
        predictions = data["predictions"]
        assert isinstance(predictions, list)

        if predictions:
            pred = predictions[0]
            assert "date" in pred
            assert "level" in pred
            assert "probability" in pred
            assert "bounds_80" in pred

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
        response = requests.get("http://localhost:8003/zones")
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
            assert "river_proximity" in zone
            assert "elevation_risk" in zone
            assert "pop_density" in zone
            assert "crit_infra_score" in zone

            # Test data types
            assert isinstance(zone["pf"], (int, float))
            assert isinstance(zone["vulnerability"], (int, float))
            assert isinstance(zone["is_critical_infra"], bool)
            assert isinstance(zone["hospital_count"], int)

        print("✅ /zones endpoint validation passed")
        return True

    except Exception as e:
        print(f"❌ /zones endpoint test failed: {e}")
        return False

def test_rule_based_dispatch_endpoint():
    """Test the /rule-based/dispatch endpoint with Allocation models."""
    print("🔍 Testing /rule-based/dispatch endpoint...")

    try:
        response = requests.get("http://localhost:8003/rule-based/dispatch")
        assert response.status_code == 200

        data = response.json()

        # Validate response structure
        assert "summary" in data
        assert "allocations" in data

        summary = data["summary"]
        assert "total_zones" in summary
        assert "zones_with_allocations" in summary
        assert "total_resources" in summary
        assert "timestamp" in summary

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
            assert "resources" in allocation

            # Test enum validation
            assert allocation["impact_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
            assert allocation["allocation_mode"] in ["FUZZY", "OPTIMISTIC", "CONSERVATIVE"]
            assert isinstance(allocation["units_allocated"], int)

        print("✅ /rule-based/dispatch endpoint validation passed")
        return True

    except Exception as e:
        print(f"❌ /rule-based/dispatch endpoint test failed: {e}")
        return False

def test_zones_geo_endpoint():
    """Test the /zones-geo endpoint for GeoJSON data."""
    print("🔍 Testing /zones-geo endpoint...")

    try:
        response = requests.get("http://localhost:8003/zones-geo")
        assert response.status_code == 200

        geo_data = response.json()

        # Validate GeoJSON structure
        assert "type" in geo_data
        assert geo_data["type"] == "FeatureCollection"
        assert "features" in geo_data
        assert isinstance(geo_data["features"], list)

        if geo_data["features"]:
            feature = geo_data["features"][0]
            assert "type" in feature
            assert "geometry" in feature
            assert "properties" in feature

            # Validate properties have zone data
            props = feature["properties"]
            assert "zone_id" in props or "ZIP" in props

        print("✅ /zones-geo endpoint validation passed")
        return True

    except Exception as e:
        print(f"❌ /zones-geo endpoint test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs."""
    print("🔍 Testing error handling...")

    try:
        # Test invalid days_ahead parameter
        response = requests.get("http://localhost:8003/predict?days_ahead=10")
        assert response.status_code == 422  # Validation error

        # Test invalid query parameters
        response = requests.get("http://localhost:8003/predict?days_ahead=abc")
        assert response.status_code == 422  # Validation error

        print("✅ Error handling validation passed")
        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all live API tests."""
    print("🧪 Live API Pydantic Integration Tests")
    print("=" * 50)
    print(f"Testing against http://localhost:8003")
    print(f"Timestamp: {datetime.now()}")
    print()

    tests = [
        ("Health Check", lambda: requests.get("http://localhost:8003/health").status_code == 200),
        ("Prediction Endpoint", test_prediction_endpoint),
        ("Zones Endpoint", test_zones_endpoint),
        ("Rule-based Dispatch", test_rule_based_dispatch_endpoint),
        ("Zones Geo Endpoint", test_zones_geo_endpoint),
        ("Error Handling", test_error_handling),
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
        print("\n🎉 All tests passed! Pydantic typing implementation is working correctly!")
        print("✅ API endpoints returning properly validated data")
        print("✅ Type safety enforced throughout the system")
        print("✅ Error handling working as expected")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)