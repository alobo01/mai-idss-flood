"""Rule-based resource allocation and zone management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pathlib import Path
import sys

# Ensure repository root is on sys.path so we can reuse shared Models/*
ROOT_DIR = Path(__file__).resolve().parents[3]  # /srv/app/ -> parents[3] == repo root in container
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from Models.zone_builder import build_zones_from_config, compute_pf_by_zone_from_global  # type: ignore
    from Models.rule_based import allocate_resources as pipeline_allocate  # type: ignore
    PIPELINE_MODELS_AVAILABLE = True
except ModuleNotFoundError:
    PIPELINE_MODELS_AVAILABLE = False
    build_zones_from_config = None  # type: ignore
    compute_pf_by_zone_from_global = None  # type: ignore
    pipeline_allocate = None  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Dict, Any, Optional
import math

from ..database import get_db
from ..models import Zone, Resource, Alert
from ..schemas import RuleBasedAllocation, ZoneAllocation, ErrorResponse

router = APIRouter()


@router.get("/rule-based/zones", response_model=List[Dict[str, Any]], tags=["Rule-based"])
async def get_rule_based_zones(
    min_population: Optional[int] = Query(None, ge=0, description="Minimum population filter"),
    max_population: Optional[int] = Query(None, ge=0, description="Maximum population filter"),
    risk_level: Optional[str] = Query(None, enum=["low", "moderate", "high", "severe"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get zones with rule-based analysis for resource allocation decisions.

    This endpoint applies business rules to zone data to determine:
    - Priority levels for resource allocation
    - Recommended resource types
    - Risk-based categorization
    """
    try:
        # Build query filters
        filters = []
        params = {}

        if min_population is not None:
            filters.append("population >= :min_population")
            params["min_population"] = min_population

        if max_population is not None:
            filters.append("population <= :max_population")
            params["max_population"] = max_population

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        query = f"""
            SELECT
                id,
                code,
                name,
                description,
                population,
                area_km2,
                admin_level,
                critical_assets,
                ST_AsGeoJSON(geometry, 6) as geometry,
                -- Calculate population density
                CASE
                    WHEN area_km2 > 0 THEN population / area_km2
                    ELSE population
                END as population_density
            FROM zones
            {where_clause}
            ORDER BY population DESC
        """

        result = await db.execute(text(query), params)
        zones = result.fetchall()

        if not zones:
            return []

        # Get current alerts for risk assessment
        alerts_query = """
            SELECT DISTINCT ON (zone_code)
                zone_code,
                severity,
                COUNT(*) as alert_count
            FROM alerts
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY zone_code, severity
            ORDER BY zone_code, severity DESC
        """

        alerts_result = await db.execute(text(alerts_query))
        alerts_by_zone = {alert.zone_code: alert for alert in alerts_result.fetchall()}

        # Get available resources
        resources_query = """
            SELECT
                type,
                status,
                COUNT(*) as count,
                SUM(CASE WHEN capabilities->>'capacity_lps' IS NOT NULL
                    THEN (capabilities->>'capacity_lps')::numeric ELSE 0 END) as total_capacity
            FROM resources
            WHERE status = 'available'
            GROUP BY type, status
        """

        resources_result = await db.execute(text(resources_query))
        available_resources = {r.type: r.count for r in resources_result.fetchall()}

        # Apply business rules to each zone
        analyzed_zones = []

        for zone in zones:
            # Rule 1: Priority based on population
            if zone.population > 50000:
                priority_score = 4  # High priority
                priority_level = "critical"
            elif zone.population > 20000:
                priority_score = 3  # Medium-high priority
                priority_level = "high"
            elif zone.population > 5000:
                priority_score = 2  # Medium priority
                priority_level = "medium"
            else:
                priority_score = 1  # Low priority
                priority_level = "low"

            # Rule 2: Risk adjustment based on active alerts
            zone_alert = alerts_by_zone.get(zone.code)
            if zone_alert:
                if zone_alert.severity == 'critical':
                    priority_score = min(priority_score + 2, 5)
                    risk_multiplier = 2.0
                elif zone_alert.severity == 'high':
                    priority_score = min(priority_score + 1, 5)
                    risk_multiplier = 1.5
                else:
                    risk_multiplier = 1.2
            else:
                risk_multiplier = 1.0

            # Rule 3: Critical assets consideration
            critical_assets_count = len(zone.critical_assets or [])
            if critical_assets_count > 5:
                priority_score = min(priority_score + 1, 5)
            elif critical_assets_count > 0:
                priority_score = min(priority_score + 0.5, 5)

            # Rule 4: Population density factor
            density_factor = 1.0
            if zone.population_density > 1000:  # High density
                density_factor = 1.3
                priority_score = min(priority_score + 0.5, 5)
            elif zone.population_density < 100:  # Low density
                density_factor = 0.8

            # Calculate final allocation priority
            final_priority = min(priority_score * risk_multiplier * density_factor, 5)

            # Determine recommended resource allocation
            recommended_resources = calculate_resource_allocation(
                zone.population,
                critical_assets_count,
                final_priority,
                available_resources
            )

            # Rule 5: Response time estimation
            response_time = estimate_response_time(zone.area_km2, final_priority)

            analyzed_zones.append({
                "zone_id": zone.code,
                "zone_name": zone.name,
                "priority_score": round(final_priority, 2),
                "priority_level": get_priority_level(final_priority),
                "population": zone.population,
                "area_km2": zone.area_km2,
                "population_density": round(zone.population_density, 2),
                "critical_assets_count": critical_assets_count,
                "critical_assets": zone.critical_assets or [],
                "recommended_resources": recommended_resources,
                "estimated_response_time_minutes": response_time,
                "risk_factors": {
                    "active_alerts": zone_alert.alert_count if zone_alert else 0,
                    "alert_severity": zone_alert.severity if zone_alert else "none",
                    "risk_multiplier": round(risk_multiplier, 2),
                    "density_factor": round(density_factor, 2)
                },
                "geometry": zone.geometry,
                "last_updated": datetime.utcnow()
            })

        # Sort by priority score (descending)
        analyzed_zones.sort(key=lambda x: x["priority_score"], reverse=True)

        return analyzed_zones

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze zones: {str(e)}")


@router.post("/rule-based/allocate", response_model=RuleBasedAllocation, tags=["Rule-based"])
async def allocate_resources_rule_based(
    allocation_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Perform rule-based resource allocation for zones.

    This endpoint implements a sophisticated allocation algorithm that considers:
    - Zone priority and risk factors
    - Resource availability and constraints
    - Optimal routing and deployment
    - Historical effectiveness data
    """
    try:
        incident_type = allocation_request.get("incident_type", "flood")
        available_resources = allocation_request.get("available_resources", {})
        zone_priorities = allocation_request.get("zone_priorities", {})
        constraints = allocation_request.get("constraints", {})

        # Get zones to allocate resources for
        zone_ids = allocation_request.get("zone_ids", [])
        if not zone_ids:
            # If no specific zones, get high-priority zones
            zones_query = """
                SELECT id, code, name, population, area_km2, critical_assets
                FROM zones
                WHERE population > 5000
                ORDER BY population DESC
                LIMIT 10
            """
        else:
            zones_query = """
                SELECT id, code, name, population, area_km2, critical_assets
                FROM zones
                WHERE code = ANY(:zone_ids)
            """
            zone_ids = list(zone_ids)  # Convert to list for SQL

        zones_result = await db.execute(
            text(zones_query),
            {"zone_ids": zone_ids} if zone_ids else {}
        )
        zones = zones_result.fetchall()

        if not zones:
            return RuleBasedAllocation(
                incident_type=incident_type,
                allocation_timestamp=datetime.utcnow(),
                zones=[],
                total_resources_allocated={},
                allocation_efficiency=0.0,
                unmet_needs=[]
            )

        # Get actual available resources from database if not provided
        if not available_resources:
            resources_query = """
                SELECT
                    type,
                    status,
                    COUNT(*) as available_count,
                    SUM(CASE WHEN capabilities->>'capacity_lps' IS NOT NULL
                        THEN (capabilities->>'capacity_lps')::numeric ELSE 0 END) as total_capacity
                FROM resources
                WHERE status = 'available'
                GROUP BY type, status
            """
            resources_result = await db.execute(text(resources_query))
            for r in resources_result.fetchall():
                available_resources[r.type] = {
                    "count": r.available_count,
                    "capacity": float(r.total_capacity) if r.total_capacity else 0
                }

        # Allocate resources using rule-based algorithm
        allocations = []
        total_allocated = {resource_type: 0 for resource_type in available_resources.keys()}
        unmet_needs = []

        # Sort zones by priority (population + custom priorities)
        def zone_priority(zone):
            base_priority = zone.population
            custom_priority = zone_priorities.get(zone.code, 1.0)
            return base_priority * custom_priority

        sorted_zones = sorted(zones, key=zone_priority, reverse=True)

        for zone in sorted_zones:
            # Calculate resource needs based on zone characteristics
            needs = calculate_zone_needs(zone, incident_type)

            # Allocate available resources
            zone_allocation = allocate_to_zone(zone, needs, available_resources, constraints)

            if zone_allocation:
                allocations.append(zone_allocation)

                # Update available resources
                for resource_type, allocated in zone_allocation.resources_allocated.items():
                    if resource_type in available_resources:
                        available_resources[resource_type]["count"] -= allocated
                        total_allocated[resource_type] += allocated

                # Check for unmet needs
                unmet = check_unmet_needs(needs, zone_allocation.resources_allocated)
                if unmet:
                    unmet_needs.extend([{
                        "zone_id": zone.code,
                        "zone_name": zone.name,
                        "resource_type": need["type"],
                        "required": need["required"],
                        "allocated": need["allocated"],
                        "shortage": need["shortage"]
                    } for need in unmet])

        # Calculate allocation efficiency
        efficiency = calculate_allocation_efficiency(allocations, zones, incident_type)

        return RuleBasedAllocation(
            incident_type=incident_type,
            allocation_timestamp=datetime.utcnow(),
            zones=allocations,
            total_resources_allocated=total_allocated,
            allocation_efficiency=efficiency,
            unmet_needs=unmet_needs[:10],  # Limit to top 10 unmet needs
            constraints_applied=constraints
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resource allocation failed: {str(e)}")


@router.get("/rule-based/pipeline", tags=["Rule-based"])
async def pipeline_rule_based_allocation(
    global_pf: float = Query(0.5, ge=0.0, le=1.0, description="Global flood probability from predictive model"),
    total_units: int = Query(12, ge=0, le=100, description="Total deployable response units"),
    mode: str = Query("crisp", pattern="^(crisp|fuzzy|proportional)$", description="Allocation mode"),
    max_units_per_zone: int = Query(6, ge=1, le=20, description="Hard cap per zone")
):
    """
    Bridge endpoint that uses the shared rule-based engine from `Models.rule_based`
    and zone definitions from `Models.zone_builder` (pipeline_v3) to produce
    per-zone allocations. This keeps the API aligned with the model logic used
    in offline pipeline runs.
    """
    if not PIPELINE_MODELS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Pipeline rule-based models not bundled in this image")
    try:
        pf_by_zone = compute_pf_by_zone_from_global(global_pf)
        zones = build_zones_from_config(pf_by_zone)
        allocations = pipeline_allocate(
            zones,
            total_units=total_units,
            mode=mode,
            max_units_per_zone=max_units_per_zone,
        )
        return {
            "global_pf": global_pf,
            "mode": mode,
            "total_units": total_units,
            "max_units_per_zone": max_units_per_zone,
            "allocations": allocations,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline rule-based allocation failed: {exc}")


def calculate_resource_allocation(population: int, critical_assets: int, priority: float, available_resources: Dict[str, int]) -> Dict[str, Any]:
    """Calculate recommended resource allocation for a zone."""
    allocation = {}

    # Base resource requirements per 1000 people
    base_requirements = {
        "crew": max(1, math.ceil(population / 5000)),
        "equipment": max(1, math.ceil(population / 10000)),
        "depot": 1 if population > 20000 else 0
    }

    # Adjust for priority level
    priority_multiplier = 1.0 + (priority - 1) * 0.3

    # Adjust for critical assets
    asset_multiplier = 1.0 + (critical_assets / 10)

    for resource_type, base_amount in base_requirements.items():
        adjusted_amount = math.ceil(base_amount * priority_multiplier * asset_multiplier)
        available = available_resources.get(resource_type, 0)
        allocation[resource_type] = min(adjusted_amount, available)

    return allocation


def estimate_response_time(area_km2: float, priority: float) -> int:
    """Estimate response time in minutes based on area and priority."""
    # Base time: 30 minutes for small areas, scales with area
    base_time = 30 + (area_km2 * 2)

    # Priority adjustment (higher priority = faster response)
    priority_adjustment = (6 - priority) * 10  # Priority 5 = fastest, 1 = slowest

    return max(15, int(base_time - priority_adjustment))


def get_priority_level(score: float) -> str:
    """Convert priority score to level name."""
    if score >= 4.0:
        return "critical"
    elif score >= 3.0:
        return "high"
    elif score >= 2.0:
        return "medium"
    else:
        return "low"


def calculate_zone_needs(zone, incident_type: str) -> List[Dict[str, Any]]:
    """Calculate resource needs for a zone based on incident type."""
    needs = []

    if incident_type == "flood":
        # Flood-specific resource needs
        needs.extend([
            {"type": "crew", "required": max(2, math.ceil(zone.population / 3000))},
            {"type": "equipment", "required": max(3, math.ceil(zone.area_km2 / 5))},
            {"type": "boat", "required": 1 if zone.area_km2 > 10 else 0}
        ])

    # General emergency needs
    needs.extend([
        {"type": "medical", "required": max(1, math.ceil(zone.population / 20000))},
        {"type": "shelter", "required": max(1, math.ceil(zone.population / 10000))}
    ])

    return needs


def allocate_to_zone(zone, needs: List[Dict[str, Any]], available_resources: Dict[str, Any], constraints: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Allocate resources to a specific zone."""
    allocated = {}

    for need in needs:
        resource_type = need["type"]
        required = need["required"]

        # Check resource availability
        if resource_type in available_resources:
            available = available_resources[resource_type].get("count", 0)
            allocated_amount = min(required, available)
            allocated[resource_type] = allocated_amount
        else:
            allocated[resource_type] = 0

    # Only return allocation if we allocated something
    if sum(allocated.values()) > 0:
        return ZoneAllocation(
            zone_id=zone.code,
            zone_name=zone.name,
            resources_allocated=allocated,
            allocation_timestamp=datetime.utcnow(),
            estimated_effectiveness=min(1.0, sum(allocated.values()) / sum(n["required"] for n in needs))
        )

    return None


def check_unmet_needs(needs: List[Dict[str, Any]], allocated: Dict[str, int]) -> List[Dict[str, Any]]:
    """Check for unmet resource needs."""
    unmet = []

    for need in needs:
        resource_type = need["type"]
        required = need["required"]
        allocated_amount = allocated.get(resource_type, 0)

        if allocated_amount < required:
            unmet.append({
                "type": resource_type,
                "required": required,
                "allocated": allocated_amount,
                "shortage": required - allocated_amount
            })

    return unmet


def calculate_allocation_efficiency(allocations: List[ZoneAllocation], zones, incident_type: str) -> float:
    """Calculate overall allocation efficiency."""
    if not allocations:
        return 0.0

    total_effectiveness = sum(alloc.estimated_effectiveness for alloc in allocations)
    average_effectiveness = total_effectiveness / len(allocations)

    # Adjust for coverage (how many zones got resources)
    coverage = len(allocations) / len(zones)

    # Combine effectiveness and coverage
    efficiency = average_effectiveness * coverage

    return round(efficiency, 3)
