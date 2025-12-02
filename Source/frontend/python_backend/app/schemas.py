"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# ============ Health Check ============

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


# ============ GeoJSON Schemas ============

class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Any


class ZoneProperties(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    population: Optional[int] = None
    critical_assets: List[str] = []
    admin_level: Optional[int] = 10


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: ZoneProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# ============ Assets ============

class AssetLocation(BaseModel):
    type: str
    coordinates: List[float]


class AssetResponse(BaseModel):
    id: UUID
    zoneId: str
    zoneUuid: UUID
    zoneName: str
    name: str
    type: str
    criticality: str
    location: Optional[AssetLocation] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    capacity: Optional[int] = None
    metadata: Dict[str, Any] = {}


# ============ Alerts ============

class AlertResponse(BaseModel):
    id: str
    zoneId: str
    severity: str
    type: str
    crewId: Optional[str] = None
    title: str
    description: str
    eta: Optional[str] = None
    status: str
    timestamp: str


class AlertAckRequest(BaseModel):
    acknowledgedBy: Optional[str] = "system"


class AlertAckResponse(BaseModel):
    success: bool
    message: str
    alert: Optional[Dict[str, Any]] = None


# ============ Resources ============

class DepotResource(BaseModel):
    id: str
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class EquipmentResource(BaseModel):
    id: str
    type: str
    subtype: Optional[str] = None
    capacity_lps: Optional[float] = None
    units: Optional[int] = None
    depot: Optional[str] = None
    status: str


class CrewResource(BaseModel):
    id: str
    name: str
    skills: List[str] = []
    depot: Optional[str] = None
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class ResourcesResponse(BaseModel):
    depots: List[DepotResource]
    equipment: List[EquipmentResource]
    crews: List[CrewResource]


# ============ Admin Resources ============

class AdminDepot(BaseModel):
    id: str
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    capacity: Optional[float] = None
    manager: Optional[str] = None
    phone: Optional[str] = None
    operatingHours: Optional[str] = None
    status: str
    zones: List[str] = []


class AdminEquipment(BaseModel):
    id: str
    type: str
    subtype: Optional[str] = None
    capacity_lps: Optional[float] = None
    units: Optional[int] = None
    depot: str = "Unassigned"
    status: str
    serialNumber: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AdminCrew(BaseModel):
    id: str
    name: str
    skills: List[str] = []
    depot: str = "Unassigned"
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    teamSize: Optional[int] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    certifications: List[str] = []


# ============ Admin Users ============

class AdminUserBase(BaseModel):
    username: str
    email: str
    firstName: str
    lastName: str
    role: str
    department: str
    phone: Optional[str] = None
    location: Optional[str] = None
    status: str = "active"
    zones: List[str] = []
    permissions: List[str] = []


class AdminUserCreate(AdminUserBase):
    pass


class AdminUserUpdate(BaseModel):
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    zones: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class AdminUserResponse(AdminUserBase):
    id: UUID
    createdAt: datetime
    updatedAt: datetime
    lastLogin: Optional[datetime] = None


# ============ Risk Thresholds ============

class RiskThresholdBase(BaseModel):
    name: str
    band: str
    minRisk: float = Field(ge=0, le=1)
    maxRisk: float = Field(ge=0, le=1)
    color: Optional[str] = None
    description: Optional[str] = None
    autoAlert: bool = False

    @field_validator('maxRisk')
    @classmethod
    def max_greater_than_min(cls, v, info):
        if 'minRisk' in info.data and v <= info.data['minRisk']:
            raise ValueError('maxRisk must be greater than minRisk')
        return v


class RiskThresholdCreate(RiskThresholdBase):
    pass


class RiskThresholdUpdate(BaseModel):
    name: Optional[str] = None
    band: Optional[str] = None
    minRisk: Optional[float] = Field(default=None, ge=0, le=1)
    maxRisk: Optional[float] = Field(default=None, ge=0, le=1)
    color: Optional[str] = None
    description: Optional[str] = None
    autoAlert: Optional[bool] = None


class RiskThresholdResponse(RiskThresholdBase):
    id: UUID


# ============ Gauge Thresholds ============

class GaugeThresholdBase(BaseModel):
    gaugeCode: str
    gaugeName: str
    alertThreshold: Optional[float] = None
    criticalThreshold: Optional[float] = None
    unit: str = "meters"
    description: Optional[str] = None


class GaugeThresholdCreate(GaugeThresholdBase):
    pass


class GaugeThresholdUpdate(BaseModel):
    gaugeCode: Optional[str] = None
    gaugeName: Optional[str] = None
    alertThreshold: Optional[float] = None
    criticalThreshold: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class GaugeThresholdResponse(GaugeThresholdBase):
    id: UUID


# ============ Alert Rules ============

class AlertRuleBase(BaseModel):
    name: str
    triggerType: str
    triggerValue: str
    severity: str
    enabled: bool = True
    channels: List[str] = ["Dashboard"]
    cooldownMinutes: int = 60
    description: Optional[str] = None


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    triggerType: Optional[str] = None
    triggerValue: Optional[str] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    channels: Optional[List[str]] = None
    cooldownMinutes: Optional[int] = None
    description: Optional[str] = None


class AlertRuleResponse(AlertRuleBase):
    id: UUID


# ============ Risk Data ============

class RiskDriver(BaseModel):
    feature: str
    contribution: float


class RiskDataResponse(BaseModel):
    zoneId: str
    risk: float
    drivers: List[RiskDriver]
    thresholdBand: str
    etaHours: int


# ============ Damage Index ============

class DamageIndexResponse(BaseModel):
    zoneId: str
    infra_index: float
    human_index: float
    notes: List[str]


# ============ Gauges ============

class GaugeResponse(BaseModel):
    id: str
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    level_m: float
    trend: str
    alert_threshold: float
    critical_threshold: float
    last_updated: Optional[str] = None


# ============ Communications ============

class CommunicationResponse(BaseModel):
    id: str
    channel: str
    from_: str = Field(alias="from")
    to: str
    priority: str
    text: str
    timestamp: str

    class Config:
        populate_by_name = True


class CommunicationCreate(BaseModel):
    channel: str
    from_: str = Field(alias="from")
    to: Optional[str] = None
    text: str
    priority: Optional[str] = "normal"
    direction: Optional[str] = "outbound"

    class Config:
        populate_by_name = True


class CommunicationCreateResponse(BaseModel):
    id: str
    channel: str
    from_: str = Field(alias="from")
    to: str
    text: str
    priority: str
    direction: str
    timestamp: str

    class Config:
        populate_by_name = True


# ============ Response Plans ============

class PlanAssignmentAction(BaseModel):
    action: Optional[str] = None
    resource: Optional[str] = None
    resourceId: Optional[str] = None
    quantity: Optional[int] = None


class PlanAssignment(BaseModel):
    zoneId: str
    priority: Optional[int] = None
    actions: List[Dict[str, Any]]
    notes: Optional[str] = None


class PlanResponse(BaseModel):
    id: UUID
    name: str
    planType: str
    status: str
    version: str
    assignments: List[Dict[str, Any]]
    coverage: Dict[str, Any]
    notes: str
    triggerConditions: Dict[str, Any]
    recommendedActions: List[Any]
    requiredResources: Dict[str, Any]
    estimatedDuration: Optional[int] = None
    priority: str
    createdAt: str
    updatedAt: str


class PlanDraftCreate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    assignments: List[PlanAssignment]
    coverage: Optional[Dict[str, Any]] = {}
    notes: Optional[str] = ""
    description: Optional[str] = None
    planType: Optional[str] = "resource_deployment"
    triggerConditions: Optional[Dict[str, Any]] = {}
    recommendedActions: Optional[List[Any]] = []
    requiredResources: Optional[Dict[str, Any]] = {}
    estimatedDuration: Optional[int] = None
    priority: Optional[str] = "medium"


# ============ Zone Update ============

class ZoneUpdateRequest(BaseModel):
    geojson: GeoJSONFeatureCollection


class ZoneUpdateResponse(BaseModel):
    success: bool
    zones: GeoJSONFeatureCollection


# ============ Export ============

class ExportThresholdsResponse(BaseModel):
    risk: List[RiskThresholdResponse]
    gauges: List[GaugeThresholdResponse]
    alerts: List[AlertRuleResponse]


class ExportResourcesResponse(BaseModel):
    depots: List[Dict[str, Any]]
    equipment: List[Dict[str, Any]]
    crews: List[Dict[str, Any]]
