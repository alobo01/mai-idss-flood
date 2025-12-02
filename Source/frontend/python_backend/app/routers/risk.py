"""Risk, damage index, and gauge endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..schemas import RiskDataResponse, DamageIndexResponse, GaugeResponse
from ..utils import format_risk_drivers, determine_risk_band, normalize_timestamp, clamp, parse_point, determine_trend

router = APIRouter(prefix="/api", tags=["Risk & Monitoring"])


@router.get("/risk", response_model=List[RiskDataResponse])
async def get_risk(
    at: Optional[str] = Query(None, description="Filter by forecast time"),
    timeHorizon: str = Query("12h", description="Time horizon filter"),
    db: AsyncSession = Depends(get_db)
):
    """Get risk assessment data."""
    try:
        horizon = timeHorizon.lower()
        params = {"horizon": horizon}
        time_filter = ""
        
        if at:
            normalized = normalize_timestamp(at)
            params["at"] = normalized
            time_filter = "AND ra.forecast_time <= :at"
        
        query = text(f"""
            SELECT
                z.code as zone_code,
                ra.risk_level,
                ra.risk_factors,
                ra.forecast_time
            FROM risk_assessments ra
            JOIN zones z ON ra.zone_id = z.id
            WHERE ra.time_horizon = :horizon
            {time_filter}
            ORDER BY ra.forecast_time DESC, ra.risk_level DESC
            LIMIT 200
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        from datetime import timezone
        now = datetime.now(timezone.utc)
        payload = []
        
        for row in rows:
            forecast_time = row.forecast_time
            if isinstance(forecast_time, datetime):
                # Make sure forecast_time is timezone-aware
                if forecast_time.tzinfo is None:
                    forecast_time = forecast_time.replace(tzinfo=timezone.utc)
                eta_hours = max(0, int((forecast_time - now).total_seconds() / 3600))
            else:
                eta_hours = 0
            
            risk_level = float(row.risk_level)
            payload.append({
                "zoneId": row.zone_code,
                "risk": risk_level,
                "drivers": format_risk_drivers(row.risk_factors),
                "thresholdBand": determine_risk_band(risk_level),
                "etaHours": eta_hours,
            })
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch risk data: {str(e)}")


@router.get("/damage-index", response_model=List[DamageIndexResponse])
async def get_damage_index(db: AsyncSession = Depends(get_db)):
    """Get damage index data for all zones."""
    try:
        # Get max population
        pop_query = text("SELECT MAX(population)::numeric AS max_pop FROM zones")
        pop_result = await db.execute(pop_query)
        pop_row = pop_result.fetchone()
        max_population = float(pop_row.max_pop or 1)
        
        query = text("""
            SELECT
                z.code as zone_code,
                z.name,
                z.population,
                COALESCE(AVG(da.damage_level), 0) AS avg_damage,
                COUNT(DISTINCT a.id) AS asset_count,
                COUNT(DISTINCT al.id) AS open_alerts,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT a.name), NULL) AS impacted_assets
            FROM zones z
            LEFT JOIN assets a ON a.zone_id = z.id
            LEFT JOIN damage_assessments da ON da.asset_id = a.id
            LEFT JOIN alerts al ON al.zone_id = z.id AND al.resolved = false
            GROUP BY z.id
            ORDER BY z.name
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        payload = []
        for row in rows:
            infra_index = clamp(float(row.avg_damage) + 0.05 * float(row.asset_count))
            human_base = float(row.population or 0) / max_population
            human_index = clamp(human_base * 0.6 + (0.2 if row.open_alerts else 0))
            
            notes = []
            impacted = row.impacted_assets or []
            for asset in impacted[:3]:
                notes.append(f"{asset} requires inspection")
            if not notes and row.open_alerts > 0:
                notes.append("Active alerts in region")
            
            payload.append({
                "zoneId": row.zone_code,
                "infra_index": round(infra_index, 2),
                "human_index": round(human_index, 2),
                "notes": notes,
            })
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch damage data: {str(e)}")


@router.get("/gauges", response_model=List[GaugeResponse])
async def get_gauges(db: AsyncSession = Depends(get_db)):
    """Get gauge readings and status."""
    try:
        query = text("""
            WITH latest_readings AS (
                SELECT
                    gr.*,
                    LAG(gr.reading_value) OVER (PARTITION BY gr.gauge_id ORDER BY gr.reading_time DESC) AS previous_value,
                    ROW_NUMBER() OVER (PARTITION BY gr.gauge_id ORDER BY gr.reading_time DESC) AS rn
                FROM gauge_readings gr
            )
            SELECT
                g.code,
                g.name,
                ST_AsGeoJSON(g.location, 6) AS location,
                g.alert_threshold,
                g.warning_threshold,
                g.metadata,
                lr.reading_value,
                lr.previous_value,
                lr.reading_time
            FROM gauges g
            LEFT JOIN latest_readings lr ON lr.gauge_id = g.id AND lr.rn = 1
            ORDER BY g.name
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        gauges = []
        for row in rows:
            location = parse_point(row.location)
            reading = float(row.reading_value or 0)
            prev = float(row.previous_value or reading)
            metadata = row.metadata or {}
            trend = determine_trend(reading, prev, metadata.get('trend'))
            
            last_updated = row.reading_time
            if isinstance(last_updated, datetime):
                last_updated = last_updated.isoformat()
            
            gauges.append({
                "id": row.code,
                "name": row.name,
                "lat": location['lat'],
                "lng": location['lng'],
                "level_m": reading,
                "trend": trend,
                "alert_threshold": float(row.warning_threshold or 0),
                "critical_threshold": float(row.alert_threshold or 0),
                "last_updated": last_updated,
            })
        
        return gauges
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch gauges: {str(e)}")
