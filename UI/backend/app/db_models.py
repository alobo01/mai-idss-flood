"""
Pydantic models for database operations and type safety.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pydantic import BaseModel, Field, validator

from .schemas import (
    RawDataRecord,
    ZoneMetadata,
    ResourceType,
    PredictionRecord,
)


class DatabaseQueryParams(BaseModel):
    """Parameters for database queries with validation."""
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Maximum number of rows to return")
    offset: Optional[int] = Field(None, ge=0, description="Number of rows to skip")
    order_by: Optional[str] = Field(None, description="Column to order by")
    order_desc: bool = Field(False, description="Whether to order in descending order")


class PredictionInsert(BaseModel):
    """Model for inserting prediction records."""
    forecast_date: str = Field(..., description="Forecast date in YYYY-MM-DD format")
    predicted_level: float = Field(..., description="Predicted river level in feet")
    flood_probability: float = Field(..., ge=0.0, le=1.0, description="Flood probability (0-1)")
    days_ahead: int = Field(default=1, ge=1, le=7, description="Days ahead for prediction")
    lower_bound_80: Optional[float] = Field(None, description="Lower bound of 80% prediction interval")
    upper_bound_80: Optional[float] = Field(None, description="Upper bound of 80% prediction interval")
    model_version: Optional[str] = Field(None, description="Model version identifier")
    model_type: Optional[str] = Field(None, description="Model type (xgboost, bayesian, lstm)")

    @validator('forecast_date')
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @validator('upper_bound_80')
    @classmethod
    def validate_bounds(cls, v, values):
        if v is not None and 'lower_bound_80' in values and values['lower_bound_80'] is not None:
            if v <= values['lower_bound_80']:
                raise ValueError('Upper bound must be greater than lower bound')
        return v


class PredictionUpdate(BaseModel):
    """Model for updating prediction records."""
    predicted_level: Optional[float] = Field(None, description="Predicted river level in feet")
    flood_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Flood probability (0-1)")
    lower_bound_80: Optional[float] = Field(None, description="Lower bound of 80% prediction interval")
    upper_bound_80: Optional[float] = Field(None, description="Upper bound of 80% prediction interval")
    model_version: Optional[str] = Field(None, description="Model version identifier")
    model_type: Optional[str] = Field(None, description="Model type")

    @validator('upper_bound_80')
    @classmethod
    def validate_bounds(cls, v, values):
        if v is not None and 'lower_bound_80' in values and values['lower_bound_80'] is not None:
            if v <= values['lower_bound_80']:
                raise ValueError('Upper bound must be greater than lower bound')
        return v


class ZoneInsert(BaseModel):
    """Model for inserting zone records."""
    zone_id: str = Field(..., description="Unique zone identifier")
    name: str = Field(..., description="Zone name")
    river_proximity: float = Field(..., ge=0.0, le=1.0, description="River proximity score (0-1)")
    elevation_risk: float = Field(..., ge=0.0, le=1.0, description="Elevation risk score (0-1)")
    pop_density: float = Field(..., ge=0.0, le=1.0, description="Population density score (0-1)")
    crit_infra_score: float = Field(..., ge=0.0, le=1.0, description="Critical infrastructure score (0-1)")
    hospital_count: int = Field(default=0, ge=0, description="Number of hospitals in zone")
    critical_infra: bool = Field(default=False, description="Whether zone contains critical infrastructure")


class ZoneUpdate(BaseModel):
    """Model for updating zone records."""
    name: Optional[str] = Field(None, description="Zone name")
    river_proximity: Optional[float] = Field(None, ge=0.0, le=1.0, description="River proximity score (0-1)")
    elevation_risk: Optional[float] = Field(None, ge=0.0, le=1.0, description="Elevation risk score (0-1)")
    pop_density: Optional[float] = Field(None, ge=0.0, le=1.0, description="Population density score (0-1)")
    crit_infra_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Critical infrastructure score (0-1)")
    hospital_count: Optional[int] = Field(None, ge=0, description="Number of hospitals in zone")
    critical_infra: Optional[bool] = Field(None, description="Whether zone contains critical infrastructure")


class ResourceTypeInsert(BaseModel):
    """Model for inserting resource type records."""
    resource_id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Resource type name")
    description: Optional[str] = Field(None, description="Resource type description")
    icon: Optional[str] = Field(None, description="Icon identifier")
    display_order: int = Field(default=0, ge=0, description="Display order in UI")
    capacity: Optional[int] = Field(None, ge=0, description="Resource capacity")


class ResourceTypeUpdate(BaseModel):
    """Model for updating resource type records."""
    name: Optional[str] = Field(None, description="Resource type name")
    description: Optional[str] = Field(None, description="Resource type description")
    icon: Optional[str] = Field(None, description="Icon identifier")
    display_order: Optional[int] = Field(None, ge=0, description="Display order in UI")
    capacity: Optional[int] = Field(None, ge=0, description="Resource capacity")


class RawDataInsert(BaseModel):
    """Model for inserting raw data records."""
    date: datetime = Field(..., description="Data timestamp")
    daily_precip: Optional[float] = Field(None, description="Daily precipitation")
    daily_temp_avg: Optional[float] = Field(None, description="Daily average temperature")
    daily_snowfall: Optional[float] = Field(None, description="Daily snowfall")
    daily_humidity: Optional[float] = Field(None, description="Daily humidity")
    daily_wind: Optional[float] = Field(None, description="Daily wind speed")
    soil_deep_30d: Optional[float] = Field(None, description="30-day deep soil moisture")
    target_level_max: Optional[float] = Field(None, description="Maximum river level")
    hermann_level: Optional[float] = Field(None, description="Hermann gauge level")
    grafton_level: Optional[float] = Field(None, description="Grafton gauge level")


# Data Access Object (DAO) classes

class PredictionDAO:
    """Data Access Object for prediction operations."""

    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> PredictionInsert:
        """Create PredictionInsert from dictionary with validation."""
        return PredictionInsert(**data)

    @staticmethod
    def create_from_record(record: PredictionRecord) -> PredictionInsert:
        """Create PredictionInsert from PredictionRecord."""
        return PredictionInsert(
            forecast_date=record.date.strftime('%Y-%m-%d'),
            predicted_level=record.predicted_level,
            flood_probability=record.flood_probability,
            days_ahead=record.days_ahead,
            lower_bound_80=record.lower_bound_80,
            upper_bound_80=record.upper_bound_80,
            model_version=record.model_version,
            model_type=record.model_type
        )

    @staticmethod
    def to_schema(record: Dict[str, Any]) -> PredictionRecord:
        """Convert database record to PredictionRecord schema."""
        return PredictionRecord(**record)


class ZoneDAO:
    """Data Access Object for zone operations."""

    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> ZoneInsert:
        """Create ZoneInsert from dictionary with validation."""
        return ZoneInsert(**data)

    @staticmethod
    def create_from_schema(zone: ZoneMetadata) -> ZoneInsert:
        """Create ZoneInsert from ZoneMetadata schema."""
        return ZoneInsert(
            zone_id=zone.zone_id,
            name=zone.name,
            river_proximity=zone.river_proximity,
            elevation_risk=zone.elevation_risk,
            pop_density=zone.pop_density,
            crit_infra_score=zone.crit_infra_score,
            hospital_count=zone.hospital_count,
            critical_infra=zone.critical_infra
        )

    @staticmethod
    def to_schema(record: Dict[str, Any]) -> ZoneMetadata:
        """Convert database record to ZoneMetadata schema."""
        return ZoneMetadata(**record)


class ResourceTypeDAO:
    """Data Access Object for resource type operations."""

    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> ResourceTypeInsert:
        """Create ResourceTypeInsert from dictionary with validation."""
        return ResourceTypeInsert(**data)

    @staticmethod
    def create_from_schema(resource: ResourceType) -> ResourceTypeInsert:
        """Create ResourceTypeInsert from ResourceType schema."""
        return ResourceTypeInsert(
            resource_id=resource.resource_id,
            name=resource.name,
            description=resource.description,
            icon=resource.icon,
            display_order=resource.display_order,
            capacity=resource.capacity
        )

    @staticmethod
    def to_schema(record: Dict[str, Any]) -> ResourceType:
        """Convert database record to ResourceType schema."""
        return ResourceType(**record)


class RawDataDAO:
    """Data Access Object for raw data operations."""

    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> RawDataInsert:
        """Create RawDataInsert from dictionary with validation."""
        return RawDataInsert(**data)

    @staticmethod
    def create_from_dataframe_row(row: pd.Series) -> RawDataInsert:
        """Create RawDataInsert from pandas DataFrame row."""
        return RawDataInsert(
            date=row['date'],
            daily_precip=row.get('daily_precip'),
            daily_temp_avg=row.get('daily_temp_avg'),
            daily_snowfall=row.get('daily_snowfall'),
            daily_humidity=row.get('daily_humidity'),
            daily_wind=row.get('daily_wind'),
            soil_deep_30d=row.get('soil_deep_30d'),
            target_level_max=row.get('target_level_max'),
            hermann_level=row.get('hermann_level'),
            grafton_level=row.get('grafton_level')
        )

    @staticmethod
    def to_schema(record: Dict[str, Any]) -> RawDataRecord:
        """Convert database record to RawDataRecord schema."""
        return RawDataRecord(**record)