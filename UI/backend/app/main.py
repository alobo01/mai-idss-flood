"""
FastAPI backend for flood prediction system
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .prediction.data_fetcher import DataFetcher
from .db import (
    get_all_zones,
    get_all_resource_types,
    get_last_30_days_raw_data,
    get_latest_prediction,
    get_prediction_history,
)
from .prediction_service import predict_next_days
from .rule_based import (
    RESOURCE_TYPES,
    build_dispatch_plan,
    build_zones_from_data,
    compute_pf_by_zone_from_global,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Flood Prediction API",
    description="Predicts Mississippi River levels at St. Louis for 1-3 days ahead",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


IMPACT_COLOR_MAP = {
    "NORMAL": "#22c55e",
    "ADVISORY": "#facc15",
    "WARNING": "#fb923c",
    "CRITICAL": "#dc2626",
}
DEFAULT_IMPACT_COLOR = "#94a3b8"


def _aggregate_resource_units(dispatch: List[Dict[str, Any]]) -> Dict[str, int]:
    totals: Dict[str, int] = {rtype: 0 for rtype in RESOURCE_TYPES}
    for zone in dispatch:
        for resource_type, count in zone.get("resource_units", {}).items():
            totals[resource_type] = totals.get(resource_type, 0) + int(count)
    return totals


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint"""
    timestamp: str = Field(description="ISO timestamp when prediction was made")
    use_real_time_api: bool = Field(description="Whether real-time API was used")
    data_source: str = Field(description="Source of input data (database or API)")
    predictions: List[Dict[str, Any]] = Field(description="List of 1-3 day predictions")
    
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
                        "conformal_interval_80pct": {
                            "lower": 11.8,
                            "median": 12.5,
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


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "message": "Flood Prediction API is running",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "docs": "/docs"
        }
    }

@app.get("/raw-data")
async def raw_data():
    """Return the most recent 30 days of raw sensor data from the database."""
    data = get_last_30_days_raw_data()
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail="No raw data found")
    return {
        "rows": data.to_dict(orient="records")
    }


@app.get("/prediction-history")
async def prediction_history(limit: int = 90):
    """Return recent stored predictions (all horizons)."""
    df = get_prediction_history(limit=limit)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No prediction history found")
    return {"rows": df.to_dict(orient="records")}


@app.post("/predict-all")
async def predict_all():
    """
    Placeholder endpoint to request predictions over all available historical data.
    Currently acknowledges the request; extend with batch logic as needed.
    """
    return {"status": "queued", "message": "Predict for all previous data request received"}


@app.get("/rule-based/dispatch")
async def rule_based_dispatch(
    total_units: int = Query(20, ge=1, le=200, description="Total deployable response units"),
    mode: str = Query(
        "fuzzy",
        pattern="^(crisp|fuzzy|proportional|optimized)$",
        description="Allocation mode used by the rule-based planner",
    ),
    lead_time: int = Query(1, ge=1, le=7, description="Lead time (days ahead) for the cached prediction"),
    max_units_per_zone: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Optional hard cap on units per zone",
    ),
    use_optimizer: bool = Query(
        False,
        description="Use LP optimizer for fair allocation (ignores total_units, uses resource capacities)",
    ),
):
    """Build a rule-based dispatch plan using the latest cached prediction."""
    latest = get_latest_prediction(days_ahead=lead_time)
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached prediction found for the {lead_time}-day horizon",
        )

    global_pf = latest.get("flood_probability")
    if global_pf is None:
        logger.warning("Latest prediction for %s-day lead time missing flood_probability", lead_time)
        global_pf = 0.0

    global_pf = max(0.0, min(1.0, float(global_pf)))

    zone_rows = get_all_zones()
    if not zone_rows:
        raise HTTPException(status_code=500, detail="No zone metadata available")

    pf_by_zone = compute_pf_by_zone_from_global(zone_rows, global_pf)
    zones = build_zones_from_data(zone_rows, pf_by_zone)
    zone_lookup = {zone.id: zone for zone in zones}
    
    # Get resource capacities if using optimizer
    resource_capacities = None
    if use_optimizer:
        resource_data = get_all_resource_types()
        resource_capacities = {r["resource_id"]: r.get("capacity", 0) for r in resource_data}
    
    dispatch = build_dispatch_plan(
        zones,
        total_units=total_units,
        mode=mode.lower(),
        max_units_per_zone=max_units_per_zone,
        use_optimizer=use_optimizer,
        resource_capacities=resource_capacities,
    )

    for allocation in dispatch:
        zone_id = allocation.get("zone_id")
        if not isinstance(zone_id, str):
            continue

        impact = allocation.get("impact_level")
        impact_key = impact if isinstance(impact, str) else ""
        allocation["impact_color"] = IMPACT_COLOR_MAP.get(impact_key, DEFAULT_IMPACT_COLOR)

        allocation["pf"] = round(pf_by_zone.get(zone_id, 0.0), 4)
        zone_meta = zone_lookup.get(zone_id)
        allocation["vulnerability"] = round(zone_meta.vulnerability, 3) if zone_meta else None
        allocation["is_critical_infra"] = zone_meta.is_critical_infra if zone_meta else None

    aggregated_resources = _aggregate_resource_units(dispatch)
    total_allocated_units = sum(zone.get("units_allocated", 0) for zone in dispatch)
    
    # Get resource type metadata
    resource_metadata = {r["resource_id"]: r for r in get_all_resource_types()}

    # Extract fairness level if using optimizer
    fairness_level = None
    if use_optimizer and dispatch:
        fairness_level = dispatch[0].get("fairness_level")
    
    return {
        "lead_time_days": lead_time,
        "mode": mode.lower(),
        "use_optimizer": use_optimizer,
        "total_units": total_units if not use_optimizer else total_allocated_units,
        "max_units_per_zone": max_units_per_zone,
        "global_flood_probability": global_pf,
        "last_prediction": latest,
        "resource_summary": {
            "total_allocated_units": total_allocated_units,
            "per_resource_type": aggregated_resources,
            "available_capacity": resource_capacities if use_optimizer else None,
        },
        "fairness_level": fairness_level,
        "resource_metadata": resource_metadata,
        "impact_color_map": IMPACT_COLOR_MAP,
        "zones": dispatch,
    }


@app.get("/zones")
async def zones():
    """
    Return zones from the database (without geometry) to drive UI lists/filters.
    """
    from .db import get_connection
    query = """
        SELECT zone_id, name, river_proximity, elevation_risk, pop_density,
               crit_infra_score, hospital_count, critical_infra
        FROM zones
        ORDER BY zone_id
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return {"rows": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load zones: {e}")


@app.get("/resource-types")
async def resource_types():
    """
    Return all available resource types with metadata (name, description, icon).
    """
    try:
        resources = get_all_resource_types()
        if not resources:
            raise HTTPException(status_code=404, detail="No resource types found")
        return {"rows": resources}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load resource types: {e}")


class ResourceCapacityUpdate(BaseModel):
    """Model for updating resource capacity"""
    capacities: Dict[str, int] = Field(description="Map of resource_id to new capacity")


@app.put("/resource-types/capacities")
async def update_resource_capacities(update: ResourceCapacityUpdate):
    """
    Update capacities for multiple resource types.
    """
    from .db import get_connection
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        updated_count = 0
        for resource_id, capacity in update.capacities.items():
            cursor.execute(
                "UPDATE resource_types SET capacity = %s WHERE resource_id = %s",
                (capacity, resource_id)
            )
            updated_count += cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Updated {updated_count} resource capacities")
        
        # Return updated resources
        resources = get_all_resource_types()
        return {
            "success": True,
            "updated_count": updated_count,
            "resources": resources
        }
    except Exception as e:
        logger.error(f"Failed to update resource capacities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update capacities: {e}")


@app.get("/gauges")
async def gauges():
    """
    Return fixed gauge locations (from DataFetcher config).
    """
    fetcher = DataFetcher()
    gauges = []
    for key, station in fetcher.stations.items():
        gauges.append({
            "id": key,
            "name": station["name"],
            "lat": station["lat"],
            "lon": station["lon"],
            "usgs_id": station["id"],
        })
    return {"rows": gauges}


@app.get("/zones-geo")
async def zones_geo():
    """
    Return GeoJSON features for zones using zip_geojson joined with zones/zip_zones.
    """
    from .db import get_connection
    query = """
        SELECT
            zg.geojson,
            zz.zone_id,
            z.name,
            z.river_proximity,
            z.elevation_risk,
            z.pop_density,
            z.crit_infra_score,
            z.hospital_count,
            z.critical_infra
        FROM zip_geojson zg
        JOIN zip_zones zz ON zz.zip_code = zg.zip_code
        LEFT JOIN zones z ON z.zone_id = zz.zone_id
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()

        features = []
        for _, row in df.iterrows():
            geo = row["geojson"]
            if isinstance(geo, str):
                geo = json.loads(geo)
            # Normalize to Feature shape
            feature = {
                "type": "Feature",
                "geometry": geo.get("geometry", geo if isinstance(geo, dict) else None),
                "properties": {
                    "zone_id": row["zone_id"],
                    "name": row["name"],
                    "river_proximity": float(row["river_proximity"]) if row["river_proximity"] is not None else None,
                    "elevation_risk": float(row["elevation_risk"]) if row["elevation_risk"] is not None else None,
                    "pop_density": float(row["pop_density"]) if row["pop_density"] is not None else None,
                    "crit_infra_score": float(row["crit_infra_score"]) if row["crit_infra_score"] is not None else None,
                    "hospital_count": int(row["hospital_count"]) if row["hospital_count"] is not None else None,
                    "critical_infra": bool(row["critical_infra"]) if row["critical_infra"] is not None else False,
                },
            }
            features.append(feature)

        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load zone geometries: {e}")


@app.get("/predict", response_model=PredictionResponse)
async def predict(
    use_real_time_api: bool = Query(
        default=False,
        description="Use real-time APIs (USGS, weather) instead of database"
    )
):
    """
    Generate flood predictions for the next 1-3 days
    
    Args:
        use_real_time_api: If True, fetch live data from APIs. If False, use database.
    
    Returns:
        PredictionResponse with predictions for 1, 2, and 3 days ahead
    
    Raises:
        HTTPException: If prediction fails or insufficient data
    """
    
    try:
        logger.info(f"Prediction request received (use_real_time_api={use_real_time_api})")
        
        # Get input data
        if use_real_time_api:
            logger.info("Fetching data from real-time APIs...")
            from Programs.data_fetcher import get_latest_data
            raw_data = get_latest_data()
            data_source = "real-time APIs (USGS, Open-Meteo)"
        else:
            logger.info("Fetching data from database...")
            raw_data = get_last_30_days_raw_data()
            data_source = "database (raw_data table)"
        
        if raw_data is None or len(raw_data) < 30:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: need 30 days, got {len(raw_data) if raw_data is not None else 0}"
            )
        
        logger.info(f"Retrieved {len(raw_data)} days of data from {data_source}")
        
        # Generate predictions for 1, 2, and 3 days
        predictions = predict_next_days(raw_data, lead_times=[1, 2, 3])
        
        logger.info(f"Successfully generated {len(predictions)} predictions")
        
        # Build response
        response = PredictionResponse(
            timestamp=datetime.now().isoformat(),
            use_real_time_api=use_real_time_api,
            data_source=data_source,
            predictions=predictions
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Try to connect to database
        from .db import test_connection
        db_healthy = test_connection()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
