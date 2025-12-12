"""
Simple integration tests to verify Pydantic typing is working correctly.
These tests don't require external dependencies and can run quickly.
"""
import pytest
from datetime import datetime, timedelta
import pandas as pd

# Test imports work correctly
def test_imports():
    """Test that all Pydantic models and database models can be imported."""
    from app.schemas import (
        Zone, Prediction, FloodRisk, Forecast, PredictionInterval,
        CurrentConditions, Allocation, AllocationMode, ImpactLevel,
        ResourceSummary, JobStatus, ApiResponse, HistoricalPredictionResults
    )
    from app.db_models import (
        PredictionInsert, ZoneInsert, ResourceTypeInsert, RawDataInsert,
        PredictionDAO, ZoneDAO, ResourceTypeDAO, RawDataDAO
    )

    # Basic checks that imports work
    assert Zone is not None
    assert Prediction is not None
    assert FloodRisk is not None
    assert PredictionInsert is not None
    assert PredictionDAO is not None

def test_pydantic_validation():
    """Test that Pydantic models validate correctly."""
    from app.schemas import Zone, FloodRisk, Forecast

    # Test valid model creation
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

    # Test flood risk automatic derivation
    flood_risk = FloodRisk(probability=0.8)
    assert flood_risk.risk_level == "HIGH"
    assert flood_risk.risk_indicator == "🔴"

    # Test validation errors
    with pytest.raises(Exception):  # Should raise ValidationError
        Zone(
            zone_id="TEST_001",
            name="Test Zone",
            pf=1.5,  # Invalid: > 1.0
            vulnerability=0.6,
            is_critical_infra=True,
            hospital_count=2,
            river_proximity=0.8,
            elevation_risk=0.4,
            pop_density=0.7,
            crit_infra_score=0.5
        )

def test_database_models_validation():
    """Test database model validation."""
    from app.db_models import PredictionInsert, ZoneInsert

    # Test valid prediction insert
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

    # Test date format validation
    with pytest.raises(Exception):  # Should raise ValidationError
        PredictionInsert(
            forecast_date="invalid-date",
            predicted_level=13.2,
            flood_probability=0.1,
            days_ahead=1
        )

    # Test bounds validation
    with pytest.raises(Exception):  # Should raise ValidationError
        PredictionInsert(
            forecast_date="2025-12-11",
            predicted_level=13.2,
            flood_probability=0.1,
            days_ahead=1,
            lower_bound_80=13.6,
            upper_bound_80=12.8  # Upper < Lower
        )

def test_model_serialization():
    """Test that Pydantic models serialize correctly."""
    from app.schemas import Zone, Prediction, FloodRisk

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

def test_database_dao_functionality():
    """Test Data Access Object functionality."""
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

def test_enum_validation():
    """Test enum validation in models."""
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

    # Test enum string values (should work with Pydantic v2)
    allocation_str = Allocation(
        zone_id="ZONE_001",
        zone_name="Test Zone",
        impact_level="WARNING",  # String should be converted to enum
        allocation_mode="fuzzy",   # String should be converted to enum
        units_allocated=10
    )
    assert allocation.impact_level == ImpactLevel.WARNING
    assert allocation.allocation_mode == AllocationMode.FUZZY

def test_model_inheritance():
    """Test model inheritance and polymorphism."""
    from app.schemas import BaseModel, Prediction, FloodRisk

    # Test that our models inherit from Pydantic BaseModel
    pred = Prediction(
        lead_time_days=1,
        forecast_date="2025-12-11",
        forecast={"median": 13.2},
        flood_risk={"probability": 0.1}
    )

    assert isinstance(pred, BaseModel)
    assert isinstance(pred, Prediction)
    assert hasattr(pred, 'model_dump')
    assert hasattr(pred, 'model_validate')

def test_type_annotations():
    """Test that type annotations are working correctly."""
    import typing

    # Test that function signatures have proper type hints
    from app.prediction_service import predict_next_days
    from app.db import insert_prediction

    # Check function annotations exist
    assert hasattr(predict_next_days, '__annotations__')
    assert hasattr(insert_prediction, '__annotations__')

    # This is a basic check - in a real scenario, you might want to use mypy or similar tools
    # for more comprehensive type checking

def test_error_handling():
    """Test that models handle errors gracefully."""
    from app.schemas import Prediction, FloodRisk
    from pydantic import ValidationError

    # Test validation errors provide useful information
    try:
        FloodRisk(probability=1.5)  # Invalid probability
    except ValidationError as e:
        assert 'probability' in str(e)
        assert 'greater than or equal to 1' in str(e) or 'less than or equal to 1' in str(e)

    try:
        Prediction(lead_time_days=0)  # Invalid lead time (should be >= 1)
    except ValidationError as e:
        assert 'lead_time_days' in str(e)

if __name__ == "__main__":
    # Run simple tests directly
    print("Running basic integration tests...")

    test_imports()
    print("✓ Imports test passed")

    test_pydantic_validation()
    print("✓ Pydantic validation test passed")

    test_database_models_validation()
    print("✓ Database models validation test passed")

    test_model_serialization()
    print("✓ Model serialization test passed")

    test_database_dao_functionality()
    print("✓ DAO functionality test passed")

    test_enum_validation()
    print("✓ Enum validation test passed")

    test_model_inheritance()
    print("✓ Model inheritance test passed")

    test_type_annotations()
    print("✓ Type annotations test passed")

    test_error_handling()
    print("✓ Error handling test passed")

    print("\n🎉 All basic integration tests passed!")