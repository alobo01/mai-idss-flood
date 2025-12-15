#!/bin/bash

# Docker-based API test for Pydantic implementation
# Tests the running API container via Docker network

set -e

echo "🐳 Docker-based API Test for Pydantic Implementation"
echo "===================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Create a simple test script
cat > test_api_pydantic.py << 'EOF'
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
EOF

# Run the test in a temporary container that connects to the docker network
echo "Running API tests via Docker..."

# Check if the flood-prediction-ui network exists
if docker network ls | grep -q flood-prediction-ui; then
    NETWORK="--network flood-prediction-ui"
else
    NETWORK="--network host"
    print_warning "Using host network (flood-prediction-ui network not found)"
fi

# Run the test container
docker run --rm \
    --name pydantic-api-test \
    $NETWORK \
    -v $(pwd)/test_api_pydantic.py:/app/test.py \
    python:3.9-slim \
    bash -c "
        pip install requests > /dev/null 2>&1 &&
        cd /app && python test.py
    "

if [ $? -eq 0 ]; then
    print_status "Docker API test passed! 🎉"
    echo ""
    echo "✅ Pydantic typing implementation verified via API"
    echo "✅ All endpoints returning properly validated responses"
    echo "✅ Type safety enforced throughout the system"
else
    print_error "Docker API test failed! ❌"
    exit 1
fi

# Clean up
rm -f test_api_pydantic.py

echo ""
print_status "API test completed successfully!"