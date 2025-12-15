"""
Pydantic schemas for type safety and validation across the backend.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class RiskLevel(str, Enum):
    """Risk level enumeration for flood predictions."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class ImpactLevel(str, Enum):
    """Impact level enumeration for resource allocation."""
    NORMAL = "NORMAL"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AllocationMode(str, Enum):
    """Resource allocation mode enumeration."""
    CRISP = "crisp"
    FUZZY = "fuzzy"
    PROPORTIONAL = "proportional"
    OPTIMIZED = "optimized"


class RuleScenario(str, Enum):
    """Scenario selector for rule-based dispatch."""
    BEST = "best"
    NORMAL = "normal"
    WORST = "worst"


# Database Models

class RawDataRecord(BaseModel):
    """Model for raw hydrological sensor data."""
    date: datetime
    daily_precip: Optional[float] = None
    daily_temp_avg: Optional[float] = None
    daily_snowfall: Optional[float] = None
    daily_humidity: Optional[float] = None
    daily_wind: Optional[float] = None
    soil_deep_30d: Optional[float] = None
    target_level_max: Optional[float] = None
    hermann_level: Optional[float] = None
    grafton_level: Optional[float] = None

    class Config:
        from_attributes = True


class ZoneMetadata(BaseModel):
    """Model for zone metadata."""
    zone_id: str
    name: str
    river_proximity: float = Field(ge=0.0, le=1.0)
    elevation_risk: float = Field(ge=0.0, le=1.0)
    pop_density: float = Field(ge=0.0, le=1.0)
    crit_infra_score: float = Field(ge=0.0, le=1.0)
    hospital_count: int = Field(ge=0)
    critical_infra: bool = False

    class Config:
        from_attributes = True


class ResourceType(BaseModel):
    """Model for resource type metadata."""
    resource_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: int = Field(ge=0)
    capacity: Optional[int] = Field(ge=0, default=None)

    class Config:
        from_attributes = True


class PredictionRecord(BaseModel):
    """Model for prediction database records."""
    date: datetime
    days_ahead: int = Field(ge=1, le=7)
    predicted_level: Optional[float] = None
    lower_bound_80: Optional[float] = None
    upper_bound_80: Optional[float] = None
    flood_probability: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    model_version: Optional[str] = None
    model_type: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Prediction API Models

class Forecast(BaseModel):
    """Model for individual forecast values."""
    median: float
    xgboost: Optional[float] = None
    bayesian: Optional[float] = None
    lstm: Optional[float] = None


class PredictionInterval(BaseModel):
    """Model for prediction intervals."""
    lower: float
    upper: float
    width: float = Field(ge=0.0)


class FloodRisk(BaseModel):
    """Model for flood risk assessment."""
    probability: float = Field(ge=0.0, le=1.0)
    threshold_ft: float = Field(default=30.0)
    risk_level: RiskLevel
    risk_indicator: str

    @model_validator(mode='before')
    def derive_risk_level(cls, values):
        """Derive risk level and indicator from probability."""
        prob = values.get('probability', 0.0)
        if prob >= 0.7:
            values['risk_level'] = RiskLevel.HIGH
            values['risk_indicator'] = '🔴'
        elif prob >= 0.3:
            values['risk_level'] = RiskLevel.MODERATE
            values['risk_indicator'] = '🟡'
        else:
            values['risk_level'] = RiskLevel.LOW
            values['risk_indicator'] = '🟢'
        return values


class CurrentConditions(BaseModel):
    """Model for current conditions in prediction response."""
    date: str
    current_level_st_louis: float


class Prediction(BaseModel):
    """Model for individual prediction."""
    lead_time_days: int = Field(ge=1, le=3)
    forecast_date: str
    current_conditions: Optional[CurrentConditions] = None
    forecast: Optional[Forecast] = None
    prediction_interval_80pct: Optional[PredictionInterval] = None
    conformal_interval_80pct: Optional[PredictionInterval] = None
    flood_risk: Optional[FloodRisk] = None
    cached: Optional[bool] = False
    cached_at: Optional[str] = None
    intervals_enriched: Optional[bool] = None
    intervals_enrichment_reason: Optional[str] = None
    error: Optional[str] = None
    base_date: Optional[str] = None
    window_start: Optional[str] = None


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint."""
    timestamp: str = Field(description="ISO timestamp when prediction was made")
    use_real_time_api: bool = Field(description="Whether real-time API was used")
    data_source: str = Field(description="Source of input data (database or API)")
    predictions: List[Prediction] = Field(description="List of 1-3 day predictions")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-10T12:00:00",
                "use_real_time_api": False,
                "data_source": "database",
                "predictions": [
                    {
                        "lead_time_days": 1,
                        "forecast_date": "2025-12-11",
                        "forecast": {
                            "median": 12.5,
                            "xgboost": 12.3,
                            "bayesian": 12.6,
                            "lstm": 12.4
                        },
                        "prediction_interval_80pct": {
                            "lower": 11.8,
                            "upper": 13.2,
                            "width": 1.4
                        },
                        "flood_risk": {
                            "probability": 0.05,
                            "threshold_ft": 30.0,
                            "risk_level": "LOW",
                            "risk_indicator": "🟢"
                        }
                    }
                ]
            }
        }


# Rule-based Models

class Zone(BaseModel):
    """Model for flood zone."""
    id: str
    name: str
    pf: float = Field(ge=0.0, le=1.0, description="Flood probability")
    vulnerability: float = Field(ge=0.0, le=1.0, description="Vulnerability score")
    is_critical_infra: bool = False
    hospital_count: int = Field(ge=0)
    river_proximity: float = Field(ge=0.0, le=1.0)
    elevation_risk: float = Field(ge=0.0, le=1.0)
    pop_density: float = Field(ge=0.0, le=1.0)
    crit_infra_score: float = Field(ge=0.0, le=1.0)


class ResourcePriority(BaseModel):
    """Model for resource priority information."""
    zone_id: str
    zone_name: str
    priority_index: float = Field(ge=0.0, le=1.0)
    resource_scores: Dict[str, float]
    resource_priority: List[str]


class Allocation(BaseModel):
    """Model for resource allocation."""
    zone_id: str
    zone_name: str
    impact_level: ImpactLevel
    impact_color: Optional[str] = None
    allocation_mode: AllocationMode
    units_allocated: int = Field(ge=0)
    max_units_per_zone: Optional[int] = Field(ge=1, default=None)
    priority_index: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    resource_priority: List[str] = Field(default_factory=list)
    resource_units: Dict[str, int] = Field(default_factory=dict)
    resource_scores: Dict[str, float] = Field(default_factory=dict)
    pf: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    vulnerability: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    vulnerability_category: Optional[str] = None
    category: Optional[str] = None
    is_critical_infra: Optional[bool] = None
    impact_factor: Optional[float] = None
    satisfaction_level: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    fairness_level: Optional[float] = Field(ge=0.0, le=1.0, default=None)


class ResourceSummary(BaseModel):
    """Model for resource allocation summary."""
    total_allocated_units: int = Field(ge=0)
    per_resource_type: Dict[str, int]
    available_capacity: Optional[Dict[str, int]] = None


class DispatchPlanResponse(BaseModel):
    """Response model for rule-based dispatch plan."""
    lead_time_days: int = Field(ge=1, le=7)
    mode: AllocationMode
    fuzzy_engine_available: bool
    use_optimizer: bool
    total_units: int = Field(ge=0)
    max_units_per_zone: Optional[int] = Field(ge=1, default=None)
    global_flood_probability: float = Field(ge=0.0, le=1.0)
    scenario: RuleScenario = Field(
        default=RuleScenario.NORMAL,
        description="Scenario (best/normal/worst) used when selecting the prediction level",
    )
    last_prediction: Optional[Dict[str, Any]] = None
    resource_summary: ResourceSummary
    fairness_level: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    resource_metadata: Dict[str, ResourceType]
    impact_color_map: Dict[str, str]
    zones: List[Allocation]


# API Request/Response Models

class PredictAllRequest(BaseModel):
    """Request model for predict-all endpoint."""
    lead_times: List[int] = Field(default=[1, 2, 3], description="Lead times in days")
    skip_cached: bool = Field(default=True, description="Skip cached predictions")
    run_in_background: bool = Field(default=False, description="Run in background")

    @field_validator('lead_times')
    @classmethod
    def validate_lead_times(cls, v):
        if not v:
            return [1, 2, 3]
        for lead_time in v:
            if not (1 <= lead_time <= 7):
                raise ValueError("Lead times must be between 1 and 7 days")
        return v


class JobStatus(BaseModel):
    """Model for background job status."""
    job_id: str
    status: str = Field(description="Job status: queued, running, completed, failed")
    percent: Optional[float] = Field(ge=0.0, le=100.0, default=None)
    completed: Optional[int] = Field(ge=0, default=None)
    total: Optional[int] = Field(ge=0, default=None)
    eta_seconds: Optional[int] = Field(ge=0, default=None)
    message: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancel_requested: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DispatchRequest(BaseModel):
    """Request model for dispatch endpoint."""
    total_units: int = Field(default=20, ge=1, le=200, description="Total deployable response units")
    mode: AllocationMode = Field(default=AllocationMode.FUZZY, description="Allocation mode")
    lead_time: int = Field(default=1, ge=1, le=7, description="Lead time (days ahead)")
    global_pf: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Global flood probability override")
    max_units_per_zone: Optional[int] = Field(default=None, ge=1, le=100, description="Max units per zone")
    use_optimizer: bool = Field(default=False, description="Use LP optimizer")


class ResourceCapacityUpdate(BaseModel):
    """Model for updating resource capacity."""
    capacities: Dict[str, int] = Field(description="Map of resource_id to new capacity")

    @field_validator('capacities')
    @classmethod
    def validate_capacities(cls, v):
        for resource_id, capacity in v.items():
            if capacity < 0:
                raise ValueError(f"Capacity for {resource_id} must be non-negative")
        return v


class ZoneParametersUpdate(BaseModel):
    """Model for updating zone parameters."""
    zones: Dict[str, Dict[str, Any]] = Field(description="Map of zone_id to updated parameters")

    @field_validator('zones')
    @classmethod
    def validate_zones(cls, v):
        for zone_id, params in v.items():
            # Validate numeric parameters are within bounds
            if 'river_proximity' in params:
                val = params['river_proximity']
                if not (0.0 <= val <= 1.0):
                    raise ValueError(f"river_proximity for {zone_id} must be between 0 and 1")
            if 'elevation_risk' in params:
                val = params['elevation_risk']
                if not (0.0 <= val <= 1.0):
                    raise ValueError(f"elevation_risk for {zone_id} must be between 0 and 1")
            if 'pop_density' in params:
                val = params['pop_density']
                if not (0.0 <= val <= 1.0):
                    raise ValueError(f"pop_density for {zone_id} must be between 0 and 1")
            if 'crit_infra_score' in params:
                val = params['crit_infra_score']
                if not (0.0 <= val <= 1.0):
                    raise ValueError(f"crit_infra_score for {zone_id} must be between 0 and 1")
            if 'hospital_count' in params:
                val = params['hospital_count']
                if not (isinstance(val, int) and val >= 0):
                    raise ValueError(f"hospital_count for {zone_id} must be a non-negative integer")
        return v


class ThresholdConfig(BaseModel):
    """Model for flood threshold configuration."""
    flood_minor: float = Field(default=16.0, ge=0, description="Minor flood level in feet")
    flood_moderate: float = Field(default=22.0, ge=0, description="Moderate flood level in feet")
    flood_major: float = Field(default=28.0, ge=0, description="Major flood level in feet")
    critical_probability: float = Field(default=0.8, ge=0, le=1, description="Critical flood probability threshold")
    warning_probability: float = Field(default=0.6, ge=0, le=1, description="Warning flood probability threshold")
    advisory_probability: float = Field(default=0.3, ge=0, le=1, description="Advisory flood probability threshold")

    @field_validator('flood_moderate')
    @classmethod
    def validate_moderate(cls, v, info):
        if v <= info.data.get('flood_minor', 0):
            raise ValueError('flood_moderate must be greater than flood_minor')
        return v

    @field_validator('flood_major')
    @classmethod
    def validate_major(cls, v, info):
        if v <= info.data.get('flood_moderate', 0):
            raise ValueError('flood_major must be greater than flood_moderate')
        return v

    @field_validator('critical_probability')
    @classmethod
    def validate_critical(cls, v, info):
        if v <= info.data.get('warning_probability', 0):
            raise ValueError('critical_probability must be greater than warning_probability')
        return v

    @field_validator('warning_probability')
    @classmethod
    def validate_warning(cls, v, info):
        if v <= info.data.get('advisory_probability', 0):
            raise ValueError('warning_probability must be greater than advisory_probability')
        return v


# Utility Models

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(description="Overall health status")
    database: Optional[str] = Field(description="Database connection status", default=None)
    error: Optional[str] = Field(description="Error message if unhealthy", default=None)
    timestamp: str = Field(description="ISO timestamp")


class ApiResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class GeoJsonFeature(BaseModel):
    """Model for GeoJSON feature."""
    type: str = Field(default="Feature")
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class GeoJsonFeatureCollection(BaseModel):
    """Model for GeoJSON feature collection."""
    type: str = Field(default="FeatureCollection")
    features: List[GeoJsonFeature]


# Historical Prediction Models

class HistoricalPredictionSummary(BaseModel):
    """Summary statistics for historical predictions."""
    count: int = Field(ge=0)
    median_predictions: Dict[str, Optional[float]]
    flood_probabilities: Dict[str, Optional[float]]


class HistoricalPredictionResults(BaseModel):
    """Results from historical prediction job."""
    status: str
    timestamp: Optional[str] = None
    lead_times: List[int]
    total_predictions: int = Field(ge=0)
    predictions_by_lead_time: Dict[int, List[Prediction]]
    skipped_cached: int = Field(ge=0)
    errors: List[str]
    summary: Dict[str, HistoricalPredictionSummary]
    cancelled: Optional[bool] = False
