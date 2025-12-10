"""Simulation endpoints for live flood monitoring."""
from datetime import datetime, timezone
import json
import math
import random
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    FloodSimulationRequest,
    FloodSimulationResponse,
    StageProbability,
    StationSimulationState,
)
from ..utils import clamp

router = APIRouter(prefix="/api", tags=["Simulation"])

# Core stations for the St. Louis corridor
STATIONS = [
    {
        "code": "07010000",
        "name": "Mississippi R. at St. Louis, MO",
        "river": "Mississippi River",
        "lat": 38.62900,
        "lng": -90.17978,
        "role": "target",
        "stages_ft": {"action": 28, "flood": 30, "moderate": 35, "major": 40},
    },
    {
        "code": "05587450",
        "name": "Mississippi R. at Grafton, IL",
        "river": "Mississippi River",
        "lat": 38.96797,
        "lng": -90.42899,
        "role": "sensor",
        "stages_ft": {"action": 27, "flood": 29},
    },
    {
        "code": "06934500",
        "name": "Missouri R. at Hermann, MO",
        "river": "Missouri River",
        "lat": 38.70981,
        "lng": -91.43850,
        "role": "sensor",
        "stages_ft": {"action": 26, "flood": 28},
    },
]


def ft_to_m(value: float) -> float:
    return round(float(value) * 0.3048, 4)


def m_to_ft(value: float) -> float:
    return round(float(value) / 0.3048, 3)


async def ensure_gauges(db: AsyncSession) -> None:
    """Ensure the three focus gauges exist."""
    for station in STATIONS:
        params = {
            "code": station["code"],
            "name": station["name"],
            "river": station["river"],
            "lng": station["lng"],
            "lat": station["lat"],
            "alert": ft_to_m(station["stages_ft"].get("flood", 0)),
            "warning": ft_to_m(station["stages_ft"].get("action", 0)),
            "meta": json.dumps(
                {
                    "usgs_id": station["code"],
                    "unit_display": "ft",
                    "stages_ft": station["stages_ft"],
                }
            ),
        }
        await db.execute(
            text(
                """
                INSERT INTO gauges (code, name, location, river_name, gauge_type, unit, alert_threshold, warning_threshold, status, metadata)
                VALUES (:code, :name, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :river, 'water_level', 'feet',
                        :alert, :warning, 'active', CAST(:meta AS jsonb))
                ON CONFLICT (code) DO NOTHING
                """
            ),
            params,
        )
    await db.commit()


async def get_latest_readings(db: AsyncSession) -> Dict[str, Dict]:
    """Return latest reading (and previous) for each station keyed by code."""
    query = text(
        """
        WITH ranked AS (
          SELECT
            g.id,
            g.code,
            g.name,
            g.alert_threshold,
            g.warning_threshold,
            g.metadata,
            gr.reading_value,
            gr.reading_time,
            LAG(gr.reading_value) OVER (PARTITION BY g.id ORDER BY gr.reading_time DESC) AS previous_value,
            ROW_NUMBER() OVER (PARTITION BY g.id ORDER BY gr.reading_time DESC) AS rn
          FROM gauges g
          LEFT JOIN gauge_readings gr ON gr.gauge_id = g.id
          WHERE g.code = ANY(:codes)
        )
        SELECT * FROM ranked WHERE rn = 1
        """
    )
    result = await db.execute(query, {"codes": [s["code"] for s in STATIONS]})
    rows = result.fetchall()

    latest = {}
    for row in rows:
        latest[row.code] = {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "alert_threshold": float(row.alert_threshold) if row.alert_threshold is not None else None,
            "warning_threshold": float(row.warning_threshold) if row.warning_threshold is not None else None,
            "metadata": row.metadata or {},
            "reading_value": float(row.reading_value) if row.reading_value is not None else None,
            "previous_value": float(row.previous_value) if row.previous_value is not None else None,
            "reading_time": row.reading_time,
        }
    return latest


def probability_to_reach(predicted_ft: float, stage_ft: float) -> float:
    """Sigmoid-based probability of reaching a stage."""
    # center the sigmoid so that reaching the stage is ~0.5 prob
    scale = 1.2
    delta = predicted_ft - stage_ft
    prob = 1 / (1 + math.exp(-delta / scale))
    return round(clamp(prob, 0, 1), 3)


def build_station_payload(
    station: Dict,
    current_ft: float,
    predicted_ft: float,
    prev_ft: float,
    reading_time: datetime,
) -> StationSimulationState:
    flood_stage = station["stages_ft"].get("flood") or station["stages_ft"].get("action", 0)
    trend = (current_ft - prev_ft) if prev_ft is not None else 0.0
    probability = probability_to_reach(predicted_ft, flood_stage)

    return StationSimulationState(
        code=station["code"],
        name=station["name"],
        role=station["role"],  # type: ignore
        current_level_ft=round(current_ft, 2),
        current_level_m=round(ft_to_m(current_ft), 3),
        predicted_level_ft=round(predicted_ft, 2),
        predicted_level_m=round(ft_to_m(predicted_ft), 3),
        probability_exceedance=probability,
        trend_ft_per_hr=round(trend, 2),
        last_updated=reading_time,
    )


@router.post("/simulations/flood/step", response_model=FloodSimulationResponse)
async def simulate_flood_step(
    request: FloodSimulationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Advance the St. Louis corridor flood simulation by one step.

    - Adds a new reading for the two upstream sensor gauges
    - Updates the target (St. Louis) gauge based on upstream trend
    - Returns probabilities for critical stages
    """
    await ensure_gauges(db)
    latest = await get_latest_readings(db)

    if not latest:
        raise HTTPException(status_code=500, detail="No gauges available for simulation")

    # Build new readings
    now = datetime.now(timezone.utc)
    intensity = max(0.2, min(request.intensity, 3.0))
    horizon_hours = request.horizon_hours

    sensor_payloads: List[StationSimulationState] = []
    sensor_deltas: List[float] = []

    # First pass: update sensor gauges
    for station in [s for s in STATIONS if s["role"] == "sensor"]:
        row = latest.get(station["code"], {})
        if not row.get("id"):
            raise HTTPException(status_code=500, detail=f"Gauge {station['code']} not initialized")
        current_ft = m_to_ft(row.get("reading_value") or ft_to_m(station["stages_ft"]["action"]))
        bump = random.uniform(0.08, 0.35) * intensity
        next_ft = round(current_ft + bump, 2)
        sensor_deltas.append(next_ft - current_ft)

        await db.execute(
            text(
                """
                INSERT INTO gauge_readings (gauge_id, reading_value, reading_time, quality_flag, metadata)
                VALUES (:gauge_id, :value, :time, 'good', CAST(:meta AS jsonb))
                """
            ),
            {
                "gauge_id": row.get("id"),
                "value": ft_to_m(next_ft),
                "time": now,
                "meta": json.dumps({"unit": "ft", "value_ft": next_ft}),
            },
        )

        sensor_payloads.append(
            build_station_payload(
                station,
                next_ft,
                next_ft + 0.6 * intensity,
                current_ft,
                now,
            )
        )

    # Target station update
    target_station = next(st for st in STATIONS if st["role"] == "target")
    target_row = latest.get(target_station["code"], {})
    if not target_row.get("id"):
        raise HTTPException(status_code=500, detail=f"Gauge {target_station['code']} not initialized")
    target_current_ft = m_to_ft(
        target_row.get("reading_value") or ft_to_m(target_station["stages_ft"]["action"])
    )
    avg_delta = sum(sensor_deltas) / max(len(sensor_deltas), 1)
    base_push = max(avg_delta * 1.2, 0.12 * intensity)
    next_target_ft = round(target_current_ft + base_push, 2)
    predicted_ft = round(next_target_ft + max(avg_delta * (horizon_hours / 3), 0.6 * intensity), 2)

    await db.execute(
        text(
            """
            INSERT INTO gauge_readings (gauge_id, reading_value, reading_time, quality_flag, metadata)
            VALUES (:gauge_id, :value, :time, 'good', CAST(:meta AS jsonb))
            """
        ),
        {
            "gauge_id": target_row.get("id"),
            "value": ft_to_m(next_target_ft),
            "time": now,
            "meta": json.dumps({"unit": "ft", "value_ft": next_target_ft, "predicted_ft": predicted_ft}),
        },
    )

    # Build stage probabilities for St. Louis
    stages: List[StageProbability] = []
    for stage_name, level_ft in target_station["stages_ft"].items():
        stages.append(
            StageProbability(
                stage=stage_name.replace("_", " ").title(),
                level_ft=float(level_ft),
                probability=probability_to_reach(predicted_ft, float(level_ft)),
            )
        )

    target_payload = build_station_payload(
        target_station,
        next_target_ft,
        predicted_ft,
        target_current_ft,
        now,
    )

    await db.commit()

    return FloodSimulationResponse(
        ticked_at=now,
        interval_seconds=request.interval_seconds,
        horizon_hours=horizon_hours,
        target_station=target_payload,
        sensor_stations=sensor_payloads,
        critical_stages=stages,
    )
