"""Database models using SQLAlchemy with PostGIS support."""
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean, 
    DateTime, ForeignKey, ARRAY, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid

from .database import Base


class Zone(Base):
    """Geographic zones with flood risk data."""
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    population = Column(Integer, default=0)
    area_km2 = Column(Numeric(10, 2))
    admin_level = Column(Integer, default=10)
    critical_assets = Column(ARRAY(Text), default=[])
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    risk_assessments = relationship("RiskAssessment", back_populates="zone", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="zone", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="zone", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="zone", cascade="all, delete-orphan")


class RiskAssessment(Base):
    """Risk assessments over time."""
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"))
    time_horizon = Column(String(10), nullable=False)  # '6h', '12h', '18h', '24h', '48h', '72h'
    forecast_time = Column(DateTime(timezone=True), nullable=False)
    risk_level = Column(Numeric(3, 2), nullable=False)
    risk_factors = Column(JSONB)  # Additional risk factors and metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    zone = relationship("Zone", back_populates="risk_assessments")

    __table_args__ = (
        CheckConstraint('risk_level >= 0 AND risk_level <= 1', name='check_risk_level_range'),
        Index('idx_risk_assessments_zone_time', 'zone_id', 'time_horizon', 'forecast_time', unique=True),
    )


class Asset(Base):
    """Critical assets and infrastructure."""
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'hospital', 'school', 'power_plant', 'bridge', etc.
    criticality = Column(String(20), default='medium')
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    address = Column(Text)
    capacity = Column(Integer)
    meta = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    zone = relationship("Zone", back_populates="assets")
    damage_assessments = relationship("DamageAssessment", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("criticality IN ('low', 'medium', 'high', 'critical')", name='check_asset_criticality'),
    )


class DamageAssessment(Base):
    """Damage assessments for assets."""
    __tablename__ = "damage_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"))
    assessment_time = Column(DateTime(timezone=True), nullable=False)
    damage_level = Column(Numeric(3, 2), nullable=False)
    damage_type = Column(String(100))
    estimated_cost = Column(Numeric(12, 2))
    status = Column(String(20), default='assessed')
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="damage_assessments")

    __table_args__ = (
        CheckConstraint('damage_level >= 0 AND damage_level <= 1', name='check_damage_level_range'),
        CheckConstraint("status IN ('assessed', 'under_repair', 'repaired', 'demolished')", name='check_damage_status'),
    )


class Resource(Base):
    """Resources (crews, equipment, facilities)."""
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'crew', 'vehicle', 'equipment', 'facility', 'depot'
    status = Column(String(20), default='available')
    location = Column(Geometry('POINT', srid=4326))
    capacity = Column(Numeric(10, 2))
    capabilities = Column(JSONB)
    contact_info = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deployments = relationship("Deployment", back_populates="resource", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('available', 'deployed', 'maintenance', 'unavailable', 'ready', 'standby', 'working', 'rest')", 
            name='check_resource_status'
        ),
    )


class Deployment(Base):
    """Resource deployments."""
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"))
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"))
    deployment_time = Column(DateTime(timezone=True), nullable=False)
    return_time = Column(DateTime(timezone=True))
    status = Column(String(20), default='active')
    assigned_tasks = Column(Text)
    actual_impact = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    resource = relationship("Resource", back_populates="deployments")
    zone = relationship("Zone", back_populates="deployments")

    __table_args__ = (
        CheckConstraint("status IN ('planned', 'active', 'completed', 'cancelled')", name='check_deployment_status'),
    )


class Alert(Base):
    """System alerts."""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"))
    severity = Column(String(20), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'flood_warning', 'resource_shortage', etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    meta = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    zone = relationship("Zone", back_populates="alerts")

    __table_args__ = (
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name='check_alert_severity'),
    )


class Communication(Base):
    """Communication logs."""
    __tablename__ = "communications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel = Column(String(50), nullable=False)
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    direction = Column(String(20), default='outbound')
    priority = Column(String(20), default='normal')
    status = Column(String(20), default='sent')
    meta = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("direction IN ('inbound', 'outbound')", name='check_comm_direction'),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name='check_comm_priority'),
        CheckConstraint("status IN ('pending', 'sent', 'delivered', 'failed')", name='check_comm_status'),
    )


class Gauge(Base):
    """River gauges and water level monitoring."""
    __tablename__ = "gauges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    river_name = Column(String(255))
    gauge_type = Column(String(50), default='water_level')
    unit = Column(String(20), default='meters')
    alert_threshold = Column(Numeric(10, 2))
    warning_threshold = Column(Numeric(10, 2))
    status = Column(String(20), default='active')
    meta = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    readings = relationship("GaugeReading", back_populates="gauge", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'maintenance', 'inactive')", name='check_gauge_status'),
    )


class GaugeReading(Base):
    """Gauge readings."""
    __tablename__ = "gauge_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gauge_id = Column(UUID(as_uuid=True), ForeignKey("gauges.id", ondelete="CASCADE"))
    reading_value = Column(Numeric(10, 4), nullable=False)
    reading_time = Column(DateTime(timezone=True), nullable=False)
    quality_flag = Column(String(20), default='good')
    meta = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    gauge = relationship("Gauge", back_populates="readings")

    __table_args__ = (
        CheckConstraint("quality_flag IN ('good', 'suspect', 'bad', 'missing')", name='check_reading_quality'),
    )


class ResponsePlan(Base):
    """Response plans."""
    __tablename__ = "response_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(50))
    description = Column(Text)
    plan_type = Column(String(50), nullable=False)  # 'evacuation', 'resource_deployment', etc.
    trigger_conditions = Column(JSONB)
    recommended_actions = Column(JSONB)
    required_resources = Column(JSONB)
    assignments = Column(JSONB)
    coverage = Column(JSONB)
    notes = Column(Text)
    estimated_duration = Column(Integer)  # in hours
    priority = Column(String(20), default='medium')
    status = Column(String(20), default='draft')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='check_plan_priority'),
        CheckConstraint("status IN ('draft', 'active', 'archived')", name='check_plan_status'),
    )


class AdminUser(Base):
    """Administrator managed users."""
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    department = Column(String(150))
    phone = Column(String(50))
    location = Column(String(150))
    status = Column(String(30), default='active')
    zones = Column(ARRAY(Text), default=[])
    permissions = Column(ARRAY(Text), default=[])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))


class AdminRiskThreshold(Base):
    """Administrator configured risk thresholds."""
    __tablename__ = "admin_risk_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    band = Column(String(50), nullable=False)
    min_risk = Column(Numeric(4, 2), nullable=False)
    max_risk = Column(Numeric(4, 2), nullable=False)
    color = Column(String(10))
    description = Column(Text)
    auto_alert = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('min_risk >= 0 AND min_risk <= 1', name='check_min_risk_range'),
        CheckConstraint('max_risk >= 0 AND max_risk <= 1', name='check_max_risk_range'),
    )


class AdminGaugeThreshold(Base):
    """Administrator configured gauge thresholds."""
    __tablename__ = "admin_gauge_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gauge_code = Column(String(50), nullable=False)
    gauge_name = Column(String(150), nullable=False)
    alert_threshold = Column(Numeric(6, 2))
    critical_threshold = Column(Numeric(6, 2))
    unit = Column(String(20), default='meters')
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminAlertRule(Base):
    """Administrator alert automation rules."""
    __tablename__ = "admin_alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    trigger_type = Column(String(100), nullable=False)
    trigger_value = Column(String(150), nullable=False)
    severity = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)
    channels = Column(ARRAY(Text), default=['Dashboard'])
    cooldown_minutes = Column(Integer, default=60)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
