"""
Pydantic integration test - verifies that our Pydantic models work correctly.
This test can run without external dependencies.
"""
import pytest
from datetime import datetime, timedelta
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_pydantic_models():
    """Test that basic Pydantic models can be imported and used."""
    try:
        from app.schemas import (
            Zone, Prediction, FloodRisk, Forecast, PredictionInterval,
            CurrentConditions, Allocation, AllocationMode, ImpactLevel,
            ResourceSummary, JobStatus, ApiResponse
        )
        from app.db_models import (
            PredictionInsert, ZoneInsert, ResourceTypeInsert, RawDataInsert,
            PredictionDAO, ZoneDAO, ResourceTypeDAO, RawDataDAO
        )
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_model_validation():
    """Test that models validate correctly."""
    try:
        from app.schemas import Zone, FloodRisk, Forecast
        from app.db_models import PredictionInsert

        # Test Zone model
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
        assert zone.zone_id == "TEST_001"
        assert zone.pf == 0.5

        # Test FloodRisk automatic derivation
        flood_risk = FloodRisk(probability=0.8)
        assert flood_risk.risk_level == "HIGH"
        assert flood_risk.risk_indicator == "🔴"

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

        return True
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False

def test_model_serialization():
    """Test that models serialize correctly."""
    try:
        from app.schemas import Zone, Prediction

        # Test model serialization
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

        zone_dict = zone.model_dump()
        assert zone_dict['zone_id'] == "TEST_001"
        assert zone_dict['pf'] == 0.5

        # Test JSON serialization
        zone_json = zone.model_dump_json()
        assert '"zone_id": "TEST_001"' in zone_json
        assert '"pf": 0.5' in zone_json

        return True
    except Exception as e:
        print(f"❌ Model serialization failed: {e}")
        return False

def test_database_dao():
    """Test Data Access Object functionality."""
    try:
        from app.schemas import Zone, ResourceType
        from app.db_models import ZoneDAO, ResourceTypeDAO

        # Test ZoneDAO
        zone_data = {
            'zone_id': 'ZONE_001',
            'name': 'Test Zone',
            'river_proximity': 0.8,
            'elevation_risk': 0.4,
            'pop_density': 0.7,
            'crit_infra_score': 0.5,
            'hospital_count': 2,
            'critical_infra': True
        }

        zone_insert = ZoneDAO.create_from_dict(zone_data)
        assert isinstance(zone_insert, ZoneInsert)
        assert zone_insert.zone_id == 'ZONE_001'

        # Test conversion back to schema
        zone_schema = ZoneDAO.to_schema(zone_data)
        assert isinstance(zone_schema, Zone)
        assert zone_schema.zone_id == 'ZONE_001'

        return True
    except Exception as e:
        print(f"❌ DAO functionality failed: {e}")
        return False

def test_type_annotations():
    """Test that type annotations are working correctly."""
    try:
        import typing

        # Test that function signatures have proper type hints
        from app.prediction_service import predict_next_days
        from app.db import insert_prediction

        # Check function annotations exist
        assert hasattr(predict_next_days, '__annotations__')
        assert hasattr(insert_prediction, '__annotations__')

        # Test return types
        pred_annotations = predict_next_days.__annotations__
        assert 'return' in pred_annotations
        # This is a basic check - in a real scenario, you might want to use mypy or similar tools

        return True
    except Exception as e:
        print(f"❌ Type annotations test failed: {e}")
        return False

def test_enum_validation():
    """Test enum validation in models."""
    try:
        from app.schemas import Allocation, AllocationMode, ImpactLevel

        # Test valid enum values
        allocation = Allocation(
            zone_id="ZONE_001",
            zone_name="Test Zone",
            impact_level=ImpactLevel.WARNING,
            allocation_mode=AllocationMode.FUZZY,
            units_allocated=10
        )
        assert allocation.impact_level == ImpactLevel.WARNING
        assert allocation.allocation_mode == AllocationMode.FUZZY

        # Test string to enum conversion (Pydantic v2)
        allocation_str = Allocation(
            zone_id="ZONE_001",
            zone_name="Test Zone",
            impact_level="WARNING",  # String should be converted to enum
            allocation_mode="fuzzy",   # String should be converted to enum
            units_allocated=10
        )
        assert allocation_str.impact_level == ImpactLevel.WARNING
        assert allocation_str.allocation_mode == AllocationMode.FUZZY

        return True
    except Exception as e:
        print(f"❌ Enum validation test failed: {e}")
        return False

def test_prediction_service_integration():
    """Test prediction service integration with Pydantic models."""
    try:
        from app.prediction_service import (
            _create_flood_risk, _create_current_conditions,
            _create_prediction_from_dict, _naive_fallback_prediction
        )
        import pandas as pd
        from datetime import datetime, timedelta

        # Test helper functions
        flood_risk = _create_flood_risk(0.3)
        assert flood_risk.probability == 0.3
        assert flood_risk.risk_level == "MODERATE"

        # Test naive fallback prediction
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = []
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'daily_precip': 0.1 + i * 0.01,
                'target_level_max': 10.0 + i * 0.1,
            })
        raw_data = pd.DataFrame(data)

        result = _naive_fallback_prediction(raw_data, 1)
        assert 'lead_time_days' in result
        assert 'forecast' in result
        assert 'flood_risk' in result
        assert result['lead_time_days'] == 1

        return True
    except Exception as e:
        print(f"❌ Prediction service integration test failed: {e}")
        return False

def test_rule_based_integration():
    """Test rule-based system integration with Pydantic models."""
    try:
        from app.rule_based.zones import (
            compute_vulnerability, compute_pf_by_zone_from_global,
            build_zones_from_data
        )
        from app.schemas import Zone

        # Test zone building
        zone_data = [
            {
                "zone_id": "ZONE_001",
                "name": "Test Zone",
                "river_proximity": 0.8,
                "elevation_risk": 0.4,
                "pop_density": 0.7,
                "crit_infra_score": 0.5,
                "hospital_count": 2,
                "critical_infra": True,
            }
        ]
        pf_by_zone = {"ZONE_001": 0.7}
        zones = build_zones_from_data(zone_data, pf_by_zone)

        assert len(zones) == 1
        assert isinstance(zones[0], Zone)
        assert zones[0].zone_id == "ZONE_001"
        assert zones[0].pf == 0.7

        return True
    except Exception as e:
        print(f"❌ Rule-based integration test failed: {e}")
        return False

def test_api_integration():
    """Test FastAPI API integration with Pydantic models."""
    try:
        # This is a basic test to ensure API imports work
        from app.main import app
        from app.schemas import PredictionResponse, ApiResponse

        # Test that the app was created successfully
        assert app is not None
        assert app.title == "Flood Prediction API"

        # Test that we can create API response models
        api_response = ApiResponse(
            success=True,
            message="Test",
            data={"test": "data"}
        )
        assert api_response.success is True
        assert api_response.message == "Test"

        return True
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return results."""
    print("🧪 Running Pydantic Integration Tests")
    print("=" * 50)

    tests = [
        ("Basic Model Imports", test_basic_pydantic_models),
        ("Model Validation", test_model_validation),
        ("Model Serialization", test_model_serialization),
        ("Database DAO", test_database_dao),
        ("Type Annotations", test_type_annotations),
        ("Enum Validation", test_enum_validation),
        ("Prediction Service Integration", test_prediction_service_integration),
        ("Rule-based Integration", test_rule_based_integration),
        ("API Integration", test_api_integration),
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
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)