#!/bin/bash

# Docker-based Pydantic integration test
# Uses the existing docker-compose.test.yml setup

set -e

echo "🐳 Docker-based Pydantic Integration Test"
echo "========================================="

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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Check if docker compose is available
if ! command -v docker compose > /dev/null 2>&1; then
    print_error "docker compose is not available."
    exit 1
fi

print_status "docker compose is available"

# Create a simple Dockerfile for Pydantic testing
cat > Dockerfile.pydantic-test << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install only required dependencies
COPY requirements.txt .

# Install core dependencies (skip testing ones to avoid network issues)
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    pydantic==2.5.3 \
    pandas==2.1.4 \
    sqlalchemy==2.0.25 \
    numpy==1.26.3 \
    psycopg2-binary==2.9.9

# Copy application code
COPY app/ ./app/
COPY tests/ ./tests/

# Create __init__.py files
RUN touch ./app/__init__.py

# Create the test script
RUN echo 'import sys
sys.path.insert(0, "/app")

def test_pydantic():
    """Core Pydantic integration test."""
    try:
        from app.schemas import (
            Zone, Prediction, FloodRisk, Forecast, PredictionInterval,
            CurrentConditions, Allocation, AllocationMode, ImpactLevel
        )
        from app.db_models import (
            PredictionInsert, ZoneInsert, ResourceTypeInsert, RawDataInsert,
            PredictionDAO, ZoneDAO, ResourceTypeDAO, RawDataDAO
        )
        print("✅ All imports successful")

        # Test model creation
        zone = Zone(
            zone_id="TEST_001",
            name="Test Zone",
            pf=0.5,
            vulnerability=0.6,
            is_critical_infra=True,
            hospital_count=2,
            river_proximity=0.8,
            elevation_risk=0.4,
            pop_density=0.7,
            crit_infra_score=0.5
        )
        print("✅ Zone model creation successful")

        # Test FloodRisk automatic derivation
        flood_risk = FloodRisk(probability=0.8)
        assert flood_risk.risk_level == "HIGH"
        assert flood_risk.risk_indicator == "🔴"
        print("✅ FloodRisk automatic derivation working")

        # Test PredictionInsert validation
        pred_insert = PredictionInsert(
            forecast_date="2025-12-11",
            predicted_level=13.2,
            flood_probability=0.1,
            days_ahead=1,
            lower_bound_80=12.8,
            upper_bound_80=13.6
        )
        assert pred_insert.forecast_date == "2025-12-11"
        assert pred_insert.predicted_level == 13.2
        print("✅ PredictionInsert validation working")

        # Test model serialization
        zone_dict = zone.model_dump()
        assert zone_dict["zone_id"] == "TEST_001"
        assert zone_dict["pf"] == 0.5
        print("✅ Model serialization working")

        # Test DAO functionality
        zone_data = {
            "zone_id": "ZONE_001",
            "name": "Test Zone",
            "river_proximity": 0.8,
            "elevation_risk": 0.4,
            "pop_density": 0.7,
            "crit_infra_score": 0.5,
            "hospital_count": 2,
            "critical_infra": True,
        }

        zone_insert = ZoneDAO.create_from_dict(zone_data)
        assert isinstance(zone_insert, ZoneInsert)
        assert zone_insert.zone_id == "ZONE_001"
        print("✅ ZoneDAO functionality working")

        # Test enum validation
        from app.schemas import Allocation, ImpactLevel

        allocation = Allocation(
            zone_id="ZONE_001",
            zone_name="Test Zone",
            impact_level=ImpactLevel.WARNING,
            allocation_mode=AllocationMode.FUZZY,
            units_allocated=10
        )
        assert allocation.impact_level == ImpactLevel.WARNING
        assert allocation.allocation_mode == AllocationMode.FUZZY
        print("✅ Enum validation working")

        print("🎉 All Pydantic tests passed!")
        return True

    except Exception as e:
        print(f"❌ Pydantic test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pydantic()
    sys.exit(0 if success else 1)
' > /app/test_pydantic.py

# Run the test
CMD ["python", "/app/test_pydantic.py"]
EOF

echo "Building Pydantic test image..."
docker build -f Dockerfile.pydantic-test -t pydantic-test . 2>/dev/null

if [ $? -ne 0 ]; then
    print_error "Failed to build Pydantic test image"
    exit 1
fi

print_status "Pydantic test image built successfully"

echo "Running Pydantic integration test..."
docker run --rm pydantic-test

if [ $? -eq 0 ]; then
    print_status "Pydantic integration test passed! 🎉"
    echo ""
    echo "✅ Pydantic typing implementation verified successfully!"
    echo "✅ All models validate correctly"
    echo "✅ Serialization working properly"
    echo "✅ Database models functioning"
    echo "✅ Enum validation working"
else
    print_error "Pydantic integration test failed! ❌"
    exit 1
fi

# Clean up
docker rmi pydantic-test >/dev/null 2>&1 || true

echo ""
print_status "Test completed successfully!"