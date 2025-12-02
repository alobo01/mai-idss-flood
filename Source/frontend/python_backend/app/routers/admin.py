"""Admin endpoints for user management, thresholds, and configuration."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from datetime import datetime
import json

from ..database import get_db
from ..schemas import (
    AdminUserResponse, AdminUserCreate, AdminUserUpdate,
    RiskThresholdResponse, RiskThresholdCreate, RiskThresholdUpdate,
    GaugeThresholdResponse, GaugeThresholdCreate, GaugeThresholdUpdate,
    AlertRuleResponse, AlertRuleCreate, AlertRuleUpdate,
    AdminDepot, AdminEquipment, AdminCrew,
    ZoneUpdateRequest, ZoneUpdateResponse,
)
from ..utils import get_role_permissions, parse_point

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============ Helper Functions ============

def map_admin_user_row(row) -> dict:
    """Map database row to AdminUser response."""
    created_at = row.created_at
    updated_at = row.updated_at
    last_login = row.last_login
    
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    if isinstance(updated_at, datetime):
        updated_at = updated_at.isoformat()
    if isinstance(last_login, datetime):
        last_login = last_login.isoformat()
    
    return {
        "id": str(row.id),
        "username": row.username,
        "email": row.email,
        "firstName": row.first_name,
        "lastName": row.last_name,
        "role": row.role,
        "department": row.department,
        "phone": row.phone,
        "location": row.location,
        "status": row.status,
        "zones": row.zones or [],
        "permissions": row.permissions or [],
        "createdAt": created_at,
        "updatedAt": updated_at,
        "lastLogin": last_login,
    }


def map_risk_threshold_row(row) -> dict:
    """Map database row to RiskThreshold response."""
    return {
        "id": str(row.id),
        "name": row.name,
        "band": row.band,
        "minRisk": float(row.min_risk),
        "maxRisk": float(row.max_risk),
        "color": row.color,
        "description": row.description,
        "autoAlert": row.auto_alert,
    }


def map_gauge_threshold_row(row) -> dict:
    """Map database row to GaugeThreshold response."""
    return {
        "id": str(row.id),
        "gaugeCode": row.gauge_code,
        "gaugeName": row.gauge_name,
        "alertThreshold": float(row.alert_threshold) if row.alert_threshold else None,
        "criticalThreshold": float(row.critical_threshold) if row.critical_threshold else None,
        "unit": row.unit,
        "description": row.description,
    }


def map_alert_rule_row(row) -> dict:
    """Map database row to AlertRule response."""
    return {
        "id": str(row.id),
        "name": row.name,
        "triggerType": row.trigger_type,
        "triggerValue": row.trigger_value,
        "severity": row.severity,
        "enabled": row.enabled,
        "channels": row.channels or [],
        "cooldownMinutes": int(row.cooldown_minutes) if row.cooldown_minutes else None,
        "description": row.description,
    }


# ============ Resource Endpoints ============

@router.get("/resources/depots", response_model=List[AdminDepot])
async def get_admin_depots(db: AsyncSession = Depends(get_db)):
    """Get all depot resources."""
    try:
        query = text("""
            SELECT
                code,
                name,
                status,
                capacity,
                capabilities,
                contact_info,
                ST_AsGeoJSON(location, 6) AS location
            FROM resources
            WHERE LOWER(type) = 'depot'
            ORDER BY name
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        depots = []
        for row in rows:
            location = parse_point(row.location)
            capabilities = row.capabilities or {}
            contact = row.contact_info or {}
            
            depots.append({
                "id": row.code,
                "name": row.name,
                "lat": location['lat'],
                "lng": location['lng'],
                "address": contact.get('address'),
                "capacity": float(row.capacity) if row.capacity else None,
                "manager": contact.get('manager') or capabilities.get('manager'),
                "phone": contact.get('phone'),
                "operatingHours": contact.get('operating_hours'),
                "status": row.status,
                "zones": capabilities.get('zones', []),
            })
        
        return depots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load depots: {str(e)}")


@router.get("/resources/equipment", response_model=List[AdminEquipment])
async def get_admin_equipment(db: AsyncSession = Depends(get_db)):
    """Get all equipment resources."""
    try:
        query = text("""
            SELECT
                code,
                name,
                status,
                capacity,
                capabilities,
                contact_info
            FROM resources
            WHERE LOWER(type) = 'equipment'
            ORDER BY code
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        equipment = []
        for row in rows:
            capabilities = row.capabilities or {}
            contact = row.contact_info or {}
            
            equipment.append({
                "id": row.code,
                "type": capabilities.get('type', row.name),
                "subtype": capabilities.get('subtype'),
                "capacity_lps": float(capabilities.get('capacity_lps')) if capabilities.get('capacity_lps') else None,
                "units": int(capabilities.get('units')) if capabilities.get('units') else None,
                "depot": capabilities.get('depot', 'Unassigned'),
                "status": row.status,
                "serialNumber": capabilities.get('serial_number') or contact.get('serial_number'),
                "manufacturer": capabilities.get('manufacturer'),
                "model": capabilities.get('model'),
            })
        
        return equipment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load equipment: {str(e)}")


@router.get("/resources/crews", response_model=List[AdminCrew])
async def get_admin_crews(db: AsyncSession = Depends(get_db)):
    """Get all crew resources."""
    try:
        query = text("""
            SELECT
                code,
                name,
                status,
                capacity,
                capabilities,
                contact_info,
                ST_AsGeoJSON(location, 6) AS location
            FROM resources
            WHERE LOWER(type) = 'crew'
            ORDER BY name
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        crews = []
        for row in rows:
            location = parse_point(row.location)
            capabilities = row.capabilities or {}
            contact = row.contact_info or {}
            
            team_size = capabilities.get('team_size')
            if team_size is None and row.capacity:
                team_size = int(row.capacity)
            elif team_size:
                team_size = int(team_size)
            
            crews.append({
                "id": row.code,
                "name": row.name,
                "skills": capabilities.get('skills', []),
                "depot": capabilities.get('depot', 'Unassigned'),
                "status": row.status,
                "lat": location['lat'],
                "lng": location['lng'],
                "teamSize": team_size,
                "leader": capabilities.get('leader') or contact.get('manager'),
                "phone": contact.get('phone'),
                "certifications": capabilities.get('certifications', []),
            })
        
        return crews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load crews: {str(e)}")


# ============ User Management ============

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get all admin users."""
    try:
        query = text("SELECT * FROM admin_users ORDER BY created_at DESC")
        result = await db.execute(query)
        rows = result.fetchall()
        return [map_admin_user_row(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load users: {str(e)}")


@router.post("/users", status_code=201)
async def create_user(
    request: AdminUserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new admin user."""
    try:
        # Check for existing user
        check_query = text("SELECT 1 FROM admin_users WHERE username = :username OR email = :email")
        existing = await db.execute(check_query, {"username": request.username, "email": request.email})
        if existing.fetchone():
            raise HTTPException(status_code=409, detail="Username or email already exists")
        
        permissions = request.permissions if request.permissions else get_role_permissions(request.role)
        
        insert_query = text("""
            INSERT INTO admin_users (username, email, first_name, last_name, role, department, phone, location, status, zones, permissions)
            VALUES (:username, :email, :first_name, :last_name, :role, :department, :phone, :location, :status, :zones, :permissions)
            RETURNING *
        """)
        
        result = await db.execute(insert_query, {
            "username": request.username,
            "email": request.email,
            "first_name": request.firstName,
            "last_name": request.lastName,
            "role": request.role,
            "department": request.department,
            "phone": request.phone,
            "location": request.location,
            "status": request.status or 'active',
            "zones": request.zones,
            "permissions": permissions,
        })
        
        row = result.fetchone()
        await db.commit()
        
        return map_admin_user_row(row)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: AdminUserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an admin user."""
    try:
        # Get existing user
        existing_query = text("SELECT * FROM admin_users WHERE id::text = :id")
        existing_result = await db.execute(existing_query, {"id": user_id})
        existing = existing_result.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Determine permissions
        next_role = request.role if request.role else existing.role
        if request.permissions is not None:
            next_permissions = request.permissions if request.permissions else get_role_permissions(next_role)
        elif request.role:
            next_permissions = get_role_permissions(next_role)
        else:
            next_permissions = existing.permissions or get_role_permissions(next_role)
        
        zones = request.zones if request.zones is not None else (existing.zones or [])
        
        update_query = text("""
            UPDATE admin_users
            SET email = COALESCE(:email, email),
                first_name = COALESCE(:first_name, first_name),
                last_name = COALESCE(:last_name, last_name),
                role = COALESCE(:role, role),
                department = COALESCE(:department, department),
                phone = COALESCE(:phone, phone),
                location = COALESCE(:location, location),
                status = COALESCE(:status, status),
                zones = :zones,
                permissions = :permissions,
                updated_at = NOW()
            WHERE id::text = :id
            RETURNING *
        """)
        
        result = await db.execute(update_query, {
            "email": request.email,
            "first_name": request.firstName,
            "last_name": request.lastName,
            "role": request.role,
            "department": request.department,
            "phone": request.phone,
            "location": request.location,
            "status": request.status,
            "zones": zones,
            "permissions": next_permissions,
            "id": user_id,
        })
        
        row = result.fetchone()
        await db.commit()
        
        return map_admin_user_row(row)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an admin user."""
    try:
        # Check user exists and role
        check_query = text("SELECT role FROM admin_users WHERE id::text = :id")
        check_result = await db.execute(check_query, {"id": user_id})
        row = check_result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        if row.role == 'Administrator':
            count_query = text("SELECT COUNT(*)::int AS count FROM admin_users WHERE role = 'Administrator'")
            count_result = await db.execute(count_query)
            count = count_result.fetchone().count
            if count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last administrator")
        
        delete_query = text("DELETE FROM admin_users WHERE id::text = :id")
        await db.execute(delete_query, {"id": user_id})
        await db.commit()
        
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


# ============ Risk Thresholds ============

@router.get("/thresholds/risk")
async def get_risk_thresholds(db: AsyncSession = Depends(get_db)):
    """Get all risk thresholds."""
    try:
        query = text("SELECT * FROM admin_risk_thresholds ORDER BY min_risk ASC")
        result = await db.execute(query)
        rows = result.fetchall()
        return [map_risk_threshold_row(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load thresholds: {str(e)}")


@router.post("/thresholds/risk", status_code=201)
async def create_risk_threshold(
    request: RiskThresholdCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new risk threshold."""
    try:
        if request.minRisk >= request.maxRisk or request.minRisk < 0 or request.maxRisk > 1:
            raise HTTPException(status_code=400, detail="Invalid risk values")
        
        query = text("""
            INSERT INTO admin_risk_thresholds (name, band, min_risk, max_risk, color, description, auto_alert)
            VALUES (:name, :band, :min_risk, :max_risk, :color, :description, :auto_alert)
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "name": request.name,
            "band": request.band,
            "min_risk": request.minRisk,
            "max_risk": request.maxRisk,
            "color": request.color,
            "description": request.description,
            "auto_alert": request.autoAlert,
        })
        
        row = result.fetchone()
        await db.commit()
        
        return map_risk_threshold_row(row)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create threshold: {str(e)}")


@router.put("/thresholds/risk/{threshold_id}")
async def update_risk_threshold(
    threshold_id: str,
    request: RiskThresholdUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a risk threshold."""
    try:
        if request.minRisk is not None and request.maxRisk is not None:
            if request.minRisk >= request.maxRisk or request.minRisk < 0 or request.maxRisk > 1:
                raise HTTPException(status_code=400, detail="Invalid risk values")
        
        query = text("""
            UPDATE admin_risk_thresholds
            SET name = COALESCE(:name, name),
                band = COALESCE(:band, band),
                min_risk = COALESCE(:min_risk, min_risk),
                max_risk = COALESCE(:max_risk, max_risk),
                color = COALESCE(:color, color),
                description = COALESCE(:description, description),
                auto_alert = COALESCE(:auto_alert, auto_alert),
                updated_at = NOW()
            WHERE id::text = :id
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "name": request.name,
            "band": request.band,
            "min_risk": request.minRisk,
            "max_risk": request.maxRisk,
            "color": request.color,
            "description": request.description,
            "auto_alert": request.autoAlert,
            "id": threshold_id,
        })
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Threshold not found")
        
        await db.commit()
        return map_risk_threshold_row(row)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update threshold: {str(e)}")


@router.delete("/thresholds/risk/{threshold_id}", status_code=204)
async def delete_risk_threshold(threshold_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a risk threshold."""
    try:
        query = text("DELETE FROM admin_risk_thresholds WHERE id::text = :id")
        result = await db.execute(query, {"id": threshold_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Threshold not found")
        
        await db.commit()
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete threshold: {str(e)}")


# ============ Gauge Thresholds ============

@router.get("/thresholds/gauges")
async def get_gauge_thresholds(db: AsyncSession = Depends(get_db)):
    """Get all gauge thresholds."""
    try:
        query = text("SELECT * FROM admin_gauge_thresholds ORDER BY gauge_name")
        result = await db.execute(query)
        rows = result.fetchall()
        return [map_gauge_threshold_row(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load gauge thresholds: {str(e)}")


@router.post("/thresholds/gauges", status_code=201)
async def create_gauge_threshold(
    request: GaugeThresholdCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new gauge threshold."""
    try:
        query = text("""
            INSERT INTO admin_gauge_thresholds (gauge_code, gauge_name, alert_threshold, critical_threshold, unit, description)
            VALUES (:gauge_code, :gauge_name, :alert_threshold, :critical_threshold, :unit, :description)
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "gauge_code": request.gaugeCode,
            "gauge_name": request.gaugeName,
            "alert_threshold": request.alertThreshold,
            "critical_threshold": request.criticalThreshold,
            "unit": request.unit or 'meters',
            "description": request.description,
        })
        
        row = result.fetchone()
        await db.commit()
        
        return map_gauge_threshold_row(row)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create gauge threshold: {str(e)}")


@router.put("/thresholds/gauges/{threshold_id}")
async def update_gauge_threshold(
    threshold_id: str,
    request: GaugeThresholdUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a gauge threshold."""
    try:
        query = text("""
            UPDATE admin_gauge_thresholds
            SET gauge_code = COALESCE(:gauge_code, gauge_code),
                gauge_name = COALESCE(:gauge_name, gauge_name),
                alert_threshold = COALESCE(:alert_threshold, alert_threshold),
                critical_threshold = COALESCE(:critical_threshold, critical_threshold),
                unit = COALESCE(:unit, unit),
                description = COALESCE(:description, description),
                updated_at = NOW()
            WHERE id::text = :id
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "gauge_code": request.gaugeCode,
            "gauge_name": request.gaugeName,
            "alert_threshold": request.alertThreshold,
            "critical_threshold": request.criticalThreshold,
            "unit": request.unit,
            "description": request.description,
            "id": threshold_id,
        })
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Gauge threshold not found")
        
        await db.commit()
        return map_gauge_threshold_row(row)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update gauge threshold: {str(e)}")


@router.delete("/thresholds/gauges/{threshold_id}", status_code=204)
async def delete_gauge_threshold(threshold_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a gauge threshold."""
    try:
        query = text("DELETE FROM admin_gauge_thresholds WHERE id::text = :id")
        result = await db.execute(query, {"id": threshold_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Gauge threshold not found")
        
        await db.commit()
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete gauge threshold: {str(e)}")


# ============ Alert Rules ============

@router.get("/alerts/rules")
async def get_alert_rules(db: AsyncSession = Depends(get_db)):
    """Get all alert rules."""
    try:
        query = text("SELECT * FROM admin_alert_rules ORDER BY created_at DESC")
        result = await db.execute(query)
        rows = result.fetchall()
        return [map_alert_rule_row(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load alert rules: {str(e)}")


@router.post("/alerts/rules", status_code=201)
async def create_alert_rule(
    request: AlertRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert rule."""
    try:
        channels = request.channels if request.channels else ['Dashboard']
        
        query = text("""
            INSERT INTO admin_alert_rules (name, trigger_type, trigger_value, severity, enabled, channels, cooldown_minutes, description)
            VALUES (:name, :trigger_type, :trigger_value, :severity, :enabled, :channels, :cooldown_minutes, :description)
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "name": request.name,
            "trigger_type": request.triggerType,
            "trigger_value": request.triggerValue,
            "severity": request.severity,
            "enabled": request.enabled,
            "channels": channels,
            "cooldown_minutes": request.cooldownMinutes or 60,
            "description": request.description,
        })
        
        row = result.fetchone()
        await db.commit()
        
        return map_alert_rule_row(row)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")


@router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    request: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an alert rule."""
    try:
        query = text("""
            UPDATE admin_alert_rules
            SET name = COALESCE(:name, name),
                trigger_type = COALESCE(:trigger_type, trigger_type),
                trigger_value = COALESCE(:trigger_value, trigger_value),
                severity = COALESCE(:severity, severity),
                enabled = COALESCE(:enabled, enabled),
                channels = COALESCE(:channels, channels),
                cooldown_minutes = COALESCE(:cooldown_minutes, cooldown_minutes),
                description = COALESCE(:description, description),
                updated_at = NOW()
            WHERE id::text = :id
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "name": request.name,
            "trigger_type": request.triggerType,
            "trigger_value": request.triggerValue,
            "severity": request.severity,
            "enabled": request.enabled,
            "channels": request.channels,
            "cooldown_minutes": request.cooldownMinutes,
            "description": request.description,
            "id": rule_id,
        })
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        await db.commit()
        return map_alert_rule_row(row)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update alert rule: {str(e)}")


@router.delete("/alerts/rules/{rule_id}", status_code=204)
async def delete_alert_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an alert rule."""
    try:
        query = text("DELETE FROM admin_alert_rules WHERE id::text = :id")
        result = await db.execute(query, {"id": rule_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        await db.commit()
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete alert rule: {str(e)}")


# ============ Zone Management ============

@router.put("/zones")
async def update_zones(
    request: ZoneUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update zones from GeoJSON."""
    try:
        geojson = request.geojson
        if geojson.type != 'FeatureCollection' or not geojson.features:
            raise HTTPException(status_code=400, detail="Invalid GeoJSON payload")
        
        for feature in geojson.features:
            props = feature.properties
            code = props.id
            
            if not code or not feature.geometry:
                raise HTTPException(status_code=400, detail="Each feature must include an id/code and geometry")
            
            geometry_json = json.dumps(feature.geometry.model_dump())
            
            update_query = text("""
                UPDATE zones
                SET name = COALESCE(:name, name),
                    description = COALESCE(:description, description),
                    population = COALESCE(:population, population),
                    admin_level = COALESCE(:admin_level, admin_level),
                    critical_assets = COALESCE(:critical_assets, critical_assets),
                    geometry = ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                    updated_at = NOW()
                WHERE code = :code
            """)
            
            result = await db.execute(update_query, {
                "code": code,
                "name": props.name,
                "description": props.description,
                "population": props.population,
                "admin_level": props.admin_level,
                "critical_assets": props.critical_assets,
                "geometry": geometry_json,
            })
            
            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail=f"Zone with code {code} not found")
        
        await db.commit()
        
        return {"success": True, "zones": geojson}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update zones: {str(e)}")


# ============ Export Endpoints ============

@router.get("/export/{export_type}")
async def export_data(export_type: str, db: AsyncSession = Depends(get_db)):
    """Export data as JSON."""
    try:
        if export_type == 'users':
            query = text("SELECT * FROM admin_users ORDER BY created_at DESC")
            result = await db.execute(query)
            rows = result.fetchall()
            data = [map_admin_user_row(row) for row in rows]
            filename = 'users.json'
        
        elif export_type == 'thresholds':
            risk_result = await db.execute(text("SELECT * FROM admin_risk_thresholds ORDER BY min_risk"))
            gauge_result = await db.execute(text("SELECT * FROM admin_gauge_thresholds ORDER BY gauge_name"))
            alert_result = await db.execute(text("SELECT * FROM admin_alert_rules ORDER BY name"))
            
            data = {
                "risk": [map_risk_threshold_row(row) for row in risk_result.fetchall()],
                "gauges": [map_gauge_threshold_row(row) for row in gauge_result.fetchall()],
                "alerts": [map_alert_rule_row(row) for row in alert_result.fetchall()],
            }
            filename = 'thresholds.json'
        
        elif export_type == 'resources':
            query = text("""
                SELECT code, name, type, status, capacity, capabilities, contact_info, ST_AsGeoJSON(location, 6) AS location
                FROM resources
                ORDER BY type, name
            """)
            result = await db.execute(query)
            rows = result.fetchall()
            
            data = {"depots": [], "equipment": [], "crews": []}
            for row in rows:
                location = parse_point(row.location)
                capabilities = row.capabilities or {}
                contact = row.contact_info or {}
                
                if row.type == 'depot':
                    data["depots"].append({
                        "id": row.code,
                        "name": row.name,
                        "status": row.status,
                        "lat": location['lat'],
                        "lng": location['lng'],
                        "capacity": float(row.capacity) if row.capacity else None,
                        "manager": contact.get('manager') or capabilities.get('manager'),
                        "phone": contact.get('phone'),
                        "address": contact.get('address'),
                        "zones": capabilities.get('zones', []),
                    })
                elif row.type == 'equipment':
                    data["equipment"].append({
                        "id": row.code,
                        "type": capabilities.get('type', row.name),
                        "subtype": capabilities.get('subtype'),
                        "capacity": capabilities.get('capacity_lps') or row.capacity,
                        "units": capabilities.get('units'),
                        "status": row.status,
                        "depot": capabilities.get('depot'),
                    })
                elif row.type == 'crew':
                    data["crews"].append({
                        "id": row.code,
                        "name": row.name,
                        "status": row.status,
                        "teamSize": capabilities.get('team_size') or row.capacity,
                        "skills": capabilities.get('skills', []),
                        "depot": capabilities.get('depot'),
                    })
            filename = 'resources.json'
        
        elif export_type == 'zones':
            query = text("""
                SELECT code, name, description, population, area_km2, admin_level, critical_assets, ST_AsGeoJSON(geometry, 6) AS geometry
                FROM zones
                ORDER BY name
            """)
            result = await db.execute(query)
            rows = result.fetchall()
            
            data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": json.loads(row.geometry),
                        "properties": {
                            "id": row.code,
                            "name": row.name,
                            "description": row.description,
                            "population": row.population,
                            "area_km2": float(row.area_km2) if row.area_km2 else None,
                            "admin_level": row.admin_level,
                            "critical_assets": row.critical_assets or [],
                        },
                    }
                    for row in rows
                ]
            }
            filename = 'zones.geojson'
        
        else:
            raise HTTPException(status_code=400, detail="Invalid export type")
        
        return Response(
            content=json.dumps(data, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")
