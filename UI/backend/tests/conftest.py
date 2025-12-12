"""
Pytest configuration and shared fixtures for the test suite.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

from app.schemas import (
    Zone,
    RawDataRecord,
    PredictionRecord,
    ResourceType,
    FloodRisk,
    Forecast,
    PredictionInterval,
    CurrentConditions,
    Prediction,
    Allocation,
    AllocationMode,
    ImpactLevel,
    ResourceSummary,
    JobStatus,
)
from app.db_models import (
    PredictionInsert,
    ZoneInsert,
    ResourceTypeInsert,
    RawDataInsert,
)


@pytest.fixture
def sample_raw_data():
    """Sample raw data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = []
    for i, date in enumerate(dates):
        data.append({
            'date': date,
            'daily_precip': 0.1 + i * 0.01,
            'daily_temp_avg': 20.0 + i * 0.1,
            'daily_snowfall': 0.0,
            'daily_humidity': 0.6 + i * 0.001,
            'daily_wind': 5.0 + i * 0.01,
            'soil_deep_30d': 0.3 + i * 0.001,
            'target_level_max': 10.0 + i * 0.1,
            'hermann_level': 9.0 + i * 0.1,
            'grafton_level': 8.0 + i * 0.1,
        })
    return pd.DataFrame(data)


@pytest.fixture
def sample_zone_data():
    """Sample zone data for testing."""
    return [
        {
            'zone_id': 'ZONE_001',
            'name': 'Downtown St. Louis',
            'river_proximity': 0.9,
            'elevation_risk': 0.3,
            'pop_density': 0.8,
            'crit_infra_score': 0.7,
            'hospital_count': 2,
            'critical_infra': True,
        },
        {
            'zone_id': 'ZONE_002',
            'name': 'West End',
            'river_proximity': 0.6,
            'elevation_risk': 0.5,
            'pop_density': 0.4,
            'crit_infra_score': 0.3,
            'hospital_count': 0,
            'critical_infra': False,
        },
        {
            'zone_id': 'ZONE_003',
            'name': 'North County',
            'river_proximity': 0.2,
            'elevation_risk': 0.8,
            'pop_density': 0.3,
            'crit_infra_score': 0.2,
            'hospital_count': 1,
            'critical_infra': False,
        },
    ]


@pytest.fixture
def sample_resource_types():
    """Sample resource types for testing."""
    return [
        {
            'resource_id': 'R1_UAV',
            'name': 'UAV Surveillance',
            'description': 'Unmanned aerial vehicles for reconnaissance',
            'icon': 'drone',
            'display_order': 1,
            'capacity': 5,
        },
        {
            'resource_id': 'R2_ENGINEERING',
            'name': 'Engineering Teams',
            'description': 'Civil engineering response teams',
            'icon': 'engineering',
            'display_order': 2,
            'capacity': 10,
        },
        {
            'resource_id': 'R3_PUMPS',
            'name': 'Water Pumps',
            'description': 'High-capacity water pumping equipment',
            'icon': 'pump',
            'display_order': 3,
            'capacity': 15,
        },
    ]


@pytest.fixture
def sample_prediction():
    """Sample prediction data for testing."""
    return {
        'lead_time_days': 1,
        'forecast_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'current_conditions': {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'current_level_st_louis': 12.5,
        },
        'forecast': {
            'median': 13.2,
            'xgboost': 13.1,
            'bayesian': 13.3,
            'lstm': 13.2,
        },
        'prediction_interval_80pct': {
            'lower': 12.8,
            'upper': 13.6,
            'width': 0.8,
        },
        'conformal_interval_80pct': {
            'lower': 12.7,
            'upper': 13.7,
            'width': 1.0,
        },
        'flood_risk': {
            'probability': 0.1,
            'threshold_ft': 30.0,
            'risk_level': 'LOW',
            'risk_indicator': '🟢',
        },
        'cached': False,
        'intervals_enriched': True,
    }


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit.return_value = None
    mock_conn.close.return_value = None
    return mock_conn, mock_cursor


@pytest.fixture
def mock_flood_predictor():
    """Mock flood predictor for testing."""
    predictor = Mock()
    predictor.predict_from_raw_data.return_value = {
        'forecast': {
            'median': 13.2,
            'xgboost': 13.1,
            'bayesian': 13.3,
            'lstm': 13.2,
        },
        'prediction_interval_80pct': {
            'lower': 12.8,
            'upper': 13.6,
            'width': 0.8,
        },
        'conformal_interval_80pct': {
            'lower': 12.7,
            'upper': 13.7,
            'width': 1.0,
        },
        'flood_risk': {
            'probability': 0.1,
            'threshold_ft': 30.0,
            'risk_level': 'LOW',
            'risk_indicator': '🟢',
        },
    }
    return predictor


@pytest.fixture
def sample_zones(sample_zone_data):
    """Create Zone objects from sample data."""
    return [Zone(**data) for data in sample_zone_data]


@pytest.fixture
def sample_typed_resource_types(sample_resource_types):
    """Create ResourceType objects from sample data."""
    return [ResourceType(**data) for data in sample_resource_types]


@pytest.fixture
def sample_prediction_record():
    """Sample prediction record from database."""
    return PredictionRecord(
        date=datetime.now() + timedelta(days=1),
        days_ahead=1,
        predicted_level=13.2,
        lower_bound_80=12.8,
        upper_bound_80=13.6,
        flood_probability=0.1,
        model_version="v1.0.0",
        model_type="ensemble",
    )


@pytest.fixture
def sample_job_status():
    """Sample job status for testing."""
    return JobStatus(
        job_id="test_job_123",
        status="running",
        percent=45.5,
        completed=450,
        total=1000,
        eta_seconds=300,
        message="Processing data...",
        created_at=datetime.now().isoformat(),
        started_at=datetime.now().isoformat(),
    )


@pytest.fixture
def sample_allocation():
    """Sample resource allocation for testing."""
    return Allocation(
        zone_id="ZONE_001",
        zone_name="Downtown St. Louis",
        impact_level=ImpactLevel.WARNING,
        impact_color="#fb923c",
        allocation_mode=AllocationMode.FUZZY,
        units_allocated=5,
        priority_index=0.7,
        resource_priority=["R1_UAV", "R2_ENGINEERING", "R3_PUMPS"],
        resource_units={"R1_UAV": 2, "R2_ENGINEERING": 2, "R3_PUMPS": 1},
        resource_scores={"R1_UAV": 0.8, "R2_ENGINEERING": 0.6, "R3_PUMPS": 0.4},
        pf=0.4,
        vulnerability=0.75,
        vulnerability_category="HIGH",
        category="HIGH",
        is_critical_infra=True,
        impact_factor=0.3,
    )


@pytest.fixture
def sample_resource_summary():
    """Sample resource summary for testing."""
    return ResourceSummary(
        total_allocated_units=15,
        per_resource_type={"R1_UAV": 5, "R2_ENGINEERING": 5, "R3_PUMPS": 5},
        available_capacity={"R1_UAV": 10, "R2_ENGINEERING": 20, "R3_PUMPS": 30},
    )