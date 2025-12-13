"""
Tests for Pydantic schemas and validation.
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

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
    ApiResponse,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
    HistoricalPredictionResults,
    HistoricalPredictionSummary,
)
from app.db_models import (
    PredictionInsert,
    ZoneInsert,
    ResourceTypeInsert,
    RawDataInsert,
)


class TestZoneSchema:
    """Test Zone schema validation."""

    def test_valid_zone(self, sample_zone_data):
        """Test creating a valid Zone."""
        zone_data = sample_zone_data[0]
        zone = Zone(**zone_data)
        assert zone.zone_id == "ZONE_001"
        assert zone.name == "Downtown St. Louis"
        assert zone.river_proximity == 0.9
        assert zone.elevation_risk == 0.3
        assert zone.pop_density == 0.8
        assert zone.crit_infra_score == 0.7
        assert zone.hospital_count == 2
        assert zone.critical_infra is True

    def test_invalid_zone_river_proximity(self, sample_zone_data):
        """Test Zone with invalid river_proximity (> 1.0)."""
        zone_data = sample_zone_data[0].copy()
        zone_data['river_proximity'] = 1.5
        with pytest.raises(ValidationError):
            Zone(**zone_data)

    def test_invalid_zone_negative_values(self, sample_zone_data):
        """Test Zone with negative values."""
        zone_data = sample_zone_data[0].copy()
        zone_data['hospital_count'] = -1
        with pytest.raises(ValidationError):
            Zone(**zone_data)


class TestResourceTypeSchema:
    """Test ResourceType schema validation."""

    def test_valid_resource_type(self, sample_resource_types):
        """Test creating a valid ResourceType."""
        resource_data = sample_resource_types[0]
        resource = ResourceType(**resource_data)
        assert resource.resource_id == "R1_UAV"
        assert resource.name == "UAV Surveillance"
        assert resource.display_order == 1
        assert resource.capacity == 5

    def test_invalid_resource_capacity(self, sample_resource_types):
        """Test ResourceType with negative capacity."""
        resource_data = sample_resource_types[0].copy()
        resource_data['capacity'] = -5
        with pytest.raises(ValidationError):
            ResourceType(**resource_data)

    def test_invalid_display_order(self, sample_resource_types):
        """Test ResourceType with negative display_order."""
        resource_data = sample_resource_types[0].copy()
        resource_data['display_order'] = -1
        with pytest.raises(ValidationError):
            ResourceType(**resource_data)


class TestPredictionSchemas:
    """Test prediction-related schemas."""

    def test_valid_flood_risk(self):
        """Test creating a valid FloodRisk."""
        flood_risk = FloodRisk(probability=0.75)
        assert flood_risk.probability == 0.75
        assert flood_risk.risk_level == "HIGH"
        assert flood_risk.risk_indicator == "🔴"

    def test_flood_risk_derived_fields(self):
        """Test that FloodRisk derives risk level correctly."""
        # Test LOW risk
        low_risk = FloodRisk(probability=0.1)
        assert low_risk.risk_level == "LOW"
        assert low_risk.risk_indicator == "🟢"

        # Test MODERATE risk
        moderate_risk = FloodRisk(probability=0.5)
        assert moderate_risk.risk_level == "MODERATE"
        assert moderate_risk.risk_indicator == "🟡"

        # Test HIGH risk
        high_risk = FloodRisk(probability=0.8)
        assert high_risk.risk_level == "HIGH"
        assert high_risk.risk_indicator == "🔴"

    def test_invalid_flood_risk_probability(self):
        """Test FloodRisk with invalid probability."""
        with pytest.raises(ValidationError):
            FloodRisk(probability=1.5)  # > 1.0

        with pytest.raises(ValidationError):
            FloodRisk(probability=-0.1)  # < 0.0

    def test_valid_forecast(self):
        """Test creating a valid Forecast."""
        forecast = Forecast(
            median=13.2,
            xgboost=13.1,
            bayesian=13.3,
            lstm=13.2
        )
        assert forecast.median == 13.2
        assert forecast.xgboost == 13.1
        assert forecast.bayesian == 13.3
        assert forecast.lstm == 13.2

    def test_valid_prediction_interval(self):
        """Test creating a valid PredictionInterval."""
        interval = PredictionInterval(
            lower=12.8,
            upper=13.6,
            width=0.8
        )
        assert interval.lower == 12.8
        assert interval.upper == 13.6
        assert interval.width == 0.8

    def test_invalid_prediction_interval_width(self):
        """Test PredictionInterval with invalid width."""
        with pytest.raises(ValidationError):
            PredictionInterval(
                lower=12.8,
                upper=13.6,
                width=-0.8  # Should be positive
            )

    def test_valid_current_conditions(self):
        """Test creating a valid CurrentConditions."""
        conditions = CurrentConditions(
            date="2025-12-10",
            current_level_st_louis=12.5
        )
        assert conditions.date == "2025-12-10"
        assert conditions.current_level_st_louis == 12.5

    def test_valid_prediction(self, sample_prediction):
        """Test creating a valid Prediction."""
        prediction = Prediction(**sample_prediction)
        assert prediction.lead_time_days == 1
        assert prediction.forecast_date == sample_prediction['forecast_date']
        assert prediction.current_conditions.current_level_st_louis == 12.5
        assert prediction.forecast.median == 13.2
        assert prediction.flood_risk.probability == 0.1
        assert prediction.cached is False
        assert prediction.intervals_enriched is True


class TestAllocationSchemas:
    """Test allocation-related schemas."""

    def test_valid_allocation(self, sample_allocation):
        """Test creating a valid Allocation."""
        allocation = sample_allocation
        assert allocation.zone_id == "ZONE_001"
        assert allocation.allocation_mode == AllocationMode.FUZZY
        assert allocation.impact_level == ImpactLevel.WARNING
        assert allocation.units_allocated == 5
        assert allocation.is_critical_infra is True

    def test_invalid_allocation_units(self, sample_allocation):
        """Test Allocation with invalid units_allocated."""
        allocation_data = sample_allocation.model_dump()
        allocation_data['units_allocated'] = -1
        with pytest.raises(ValidationError):
            Allocation(**allocation_data)

    def test_valid_resource_summary(self, sample_resource_summary):
        """Test creating a valid ResourceSummary."""
        summary = sample_resource_summary
        assert summary.total_allocated_units == 15
        assert summary.per_resource_type["R1_UAV"] == 5
        assert summary.available_capacity["R1_UAV"] == 10

    def test_invalid_resource_summary_units(self, sample_resource_summary):
        """Test ResourceSummary with negative total_allocated_units."""
        summary_data = sample_resource_summary.model_dump()
        summary_data['total_allocated_units'] = -1
        with pytest.raises(ValidationError):
            ResourceSummary(**summary_data)


class TestJobStatusSchema:
    """Test JobStatus schema validation."""

    def test_valid_job_status(self, sample_job_status):
        """Test creating a valid JobStatus."""
        job = sample_job_status
        assert job.job_id == "test_job_123"
        assert job.status == "running"
        assert job.percent == 45.5
        assert job.completed == 450
        assert job.total == 1000
        assert job.cancel_requested is False

    def test_invalid_job_status_percent(self, sample_job_status):
        """Test JobStatus with invalid percent (> 100)."""
        job_data = sample_job_status.model_dump()
        job_data['percent'] = 150.0
        with pytest.raises(ValidationError):
            JobStatus(**job_data)

    def test_invalid_job_status_completed_negative(self, sample_job_status):
        """Test JobStatus with negative completed count."""
        job_data = sample_job_status.model_dump()
        job_data['completed'] = -10
        with pytest.raises(ValidationError):
            JobStatus(**job_data)


class TestApiSchemas:
    """Test API response schemas."""

    def test_valid_api_response(self):
        """Test creating a valid ApiResponse."""
        response = ApiResponse(
            success=True,
            message="Operation completed successfully",
            data={"key": "value"}
        )
        assert response.success is True
        assert response.message == "Operation completed successfully"
        assert response.data["key"] == "value"

    def test_valid_geojson_feature(self):
        """Test creating a valid GeoJsonFeature."""
        feature = GeoJsonFeature(
            geometry={"type": "Point", "coordinates": [-90.1994, 38.6270]},
            properties={"name": "St. Louis", "zone_id": "ZONE_001"}
        )
        assert feature.type == "Feature"
        assert feature.geometry["type"] == "Point"
        assert feature.properties["zone_id"] == "ZONE_001"

    def test_valid_geojson_feature_collection(self):
        """Test creating a valid GeoJsonFeatureCollection."""
        features = [
            GeoJsonFeature(
                geometry={"type": "Point", "coordinates": [-90.1994, 38.6270]},
                properties={"name": "St. Louis", "zone_id": "ZONE_001"}
            ),
            GeoJsonFeature(
                geometry={"type": "Point", "coordinates": [-90.2000, 38.6300]},
                properties={"name": "West End", "zone_id": "ZONE_002"}
            )
        ]
        collection = GeoJsonFeatureCollection(features=features)
        assert collection.type == "FeatureCollection"
        assert len(collection.features) == 2


class TestDatabaseModels:
    """Test database-specific Pydantic models."""

    def test_valid_prediction_insert(self):
        """Test creating a valid PredictionInsert."""
        pred = PredictionInsert(
            forecast_date="2025-12-11",
            predicted_level=13.2,
            flood_probability=0.1,
            days_ahead=1,
            lower_bound_80=12.8,
            upper_bound_80=13.6
        )
        assert pred.forecast_date == "2025-12-11"
        assert pred.predicted_level == 13.2
        assert pred.flood_probability == 0.1
        assert pred.days_ahead == 1

    def test_invalid_prediction_insert_date(self):
        """Test PredictionInsert with invalid date format."""
        with pytest.raises(ValidationError):
            PredictionInsert(
                forecast_date="invalid-date",
                predicted_level=13.2,
                flood_probability=0.1,
                days_ahead=1
            )

    def test_invalid_prediction_insert_probability(self):
        """Test PredictionInsert with invalid probability."""
        with pytest.raises(ValidationError):
            PredictionInsert(
                forecast_date="2025-12-11",
                predicted_level=13.2,
                flood_probability=1.5,  # > 1.0
                days_ahead=1
            )

    def test_invalid_prediction_insert_bounds(self):
        """Test PredictionInsert with invalid bounds (upper <= lower)."""
        with pytest.raises(ValidationError):
            PredictionInsert(
                forecast_date="2025-12-11",
                predicted_level=13.2,
                flood_probability=0.1,
                days_ahead=1,
                lower_bound_80=13.6,
                upper_bound_80=12.8  # Upper should be greater than lower
            )

    def test_valid_zone_insert(self, sample_zone_data):
        """Test creating a valid ZoneInsert."""
        zone_data = sample_zone_data[0]
        zone = ZoneInsert(**zone_data)
        assert zone.zone_id == "ZONE_001"
        assert zone.river_proximity == 0.9
        assert zone.hospital_count == 2

    def test_valid_resource_type_insert(self, sample_resource_types):
        """Test creating a valid ResourceTypeInsert."""
        resource_data = sample_resource_types[0]
        resource = ResourceTypeInsert(**resource_data)
        assert resource.resource_id == "R1_UAV"
        assert resource.display_order == 1
        assert resource.capacity == 5

    def test_valid_raw_data_insert(self):
        """Test creating a valid RawDataInsert."""
        raw_data = RawDataInsert(
            date=datetime.now(),
            daily_precip=0.5,
            daily_temp_avg=25.0,
            target_level_max=12.5
        )
        assert raw_data.daily_precip == 0.5
        assert raw_data.daily_temp_avg == 25.0
        assert raw_data.target_level_max == 12.5