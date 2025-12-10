"""Prediction endpoints for river levels and flood risk."""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import math
import os
import sys

from ..schemas import RiverLevelPrediction, FloodRiskPrediction, ErrorResponse
from ..config import get_settings
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import pandas as pd

# Make Programs/ importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if REPO_ROOT not in sys.path:
  sys.path.insert(0, REPO_ROOT)

try:
    from Programs.inference_api import FloodPredictorV2  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError(f"Failed to load inference models: {exc}") from exc

router = APIRouter()

TARGET_GAUGE_CODE = "07010000"
TARGET_GAUGE_NAME = "Mississippi R. at St. Louis, MO"
TARGET_RIVER = "Mississippi River"
FLOOD_STAGE_FT = 30.0


def risk_level_from_prob(prob: float) -> str:
    if prob >= 0.7:
        return "severe"
    if prob >= 0.4:
        return "moderate"
    return "low"


@router.get("/predict/river-level", response_model=List[RiverLevelPrediction], tags=["Predictions"])
async def predict_river_level(db: AsyncSession = Depends(get_db)) -> List[RiverLevelPrediction]:
    """
    Predict river level for St. Louis gauge (USGS 07010000) using the trained
    production models defined in Programs/inference_api.py. No mock data used.
    """
    try:
        settings = get_settings()
        predictor = FloodPredictorV2(lead_time_days=1)

        if settings.prediction_source.lower() == "db":
            df = await _fetch_ld1_history(db, settings.ld1_table)
            if df.empty or len(df) < 30:
                raise HTTPException(status_code=400, detail="Not enough LD1 history rows in database (need >=30)")
            result: Dict[str, Any] = predictor.predict_from_raw_data(df)
        else:
            result: Dict[str, Any] = predictor.predict_live()

        # Expect keys: conformal_lower/median/upper, flood_prob, current_conditions
        median_ft = float(result.get("conformal_median", result.get("median_ft", 0.0)))
        flood_prob = float(result.get("flood_probability", result.get("flood_prob", 0.0)))
        trend_ft_per_day = float(result.get("trend_ft_per_day", 0.0))
        current = result.get("current_conditions", {})
        latest_ft = float(current.get("target_level", current.get("latest_level_ft", 0.0)))
        datapoints = int(result.get("data_points_used", current.get("data_points_used", 0)) or 0)

        prediction_time = datetime.now(timezone.utc) + timedelta(hours=24)
        trend_ft_per_hr = trend_ft_per_day / 24.0

        payload = RiverLevelPrediction(
            gauge_id=TARGET_GAUGE_CODE,
            gauge_name=TARGET_GAUGE_NAME,
            river_name=TARGET_RIVER,
            prediction_time=prediction_time,
            predicted_level=round(median_ft, 2),
            confidence_level=0.9,  # model-based; we assume high since ensemble + calibration
            risk_level=risk_level_from_prob(flood_prob),
            trend_per_hour=round(trend_ft_per_hr, 3),
            data_points_used=max(datapoints, 1),
        )

        return [payload]

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")


async def _fetch_ld1_history(db: AsyncSession, table_name: str) -> pd.DataFrame:
    """Fetch last 35 days from ld1_history table."""
    query = text(f"""
        SELECT *
        FROM {table_name}
        WHERE date >= CURRENT_DATE - INTERVAL '40 days'
        ORDER BY date
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # ensure date column datetime
    if 'date' in df:
        df['date'] = pd.to_datetime(df['date'])
    return df


@router.post("/predict/flood-risk", response_model=Dict[str, Any], tags=["Predictions"])
async def predict_flood_risk(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Predict flood risk for zones based on various factors.

    This endpoint analyzes multiple data sources to generate flood risk predictions:
    - River gauge levels and trends
    - Historical flood data
    - Weather patterns (if available)
    - Zone characteristics
    """
    try:
        zone_ids = request.get('zone_ids', [])
        time_horizon = request.get('time_horizon', 24)

        # Get zone information
        zone_filter = ""
        params = {"time_horizon": time_horizon}

        if zone_ids:
            zone_filter = "WHERE code = ANY(:zone_ids)"
            params["zone_ids"] = zone_ids

        query = f"""
            SELECT
                id,
                code,
                name,
                population,
                area_km2,
                critical_assets,
                ST_AsGeoJSON(geometry) as geometry
            FROM zones
            {zone_filter}
            ORDER BY name
        """

        result = await db.execute(text(query), params)
        zones = result.fetchall()

        if not zones:
            return {"zones": [], "metadata": {"time_horizon": time_horizon, "generated_at": datetime.utcnow()}}

        # Get recent river levels for risk calculation
        gauge_query = """
            SELECT DISTINCT ON (g.id)
                g.id,
                g.code,
                g.name,
                g.alert_threshold,
                g.warning_threshold,
                gr.reading_value,
                gr.reading_time
            FROM gauges g
            LEFT JOIN gauge_readings gr ON g.id = gr.gauge_id
                AND gr.reading_time >= NOW() - INTERVAL '24 hours'
                AND gr.quality_flag = 'good'
            ORDER BY g.id, gr.reading_time DESC
        """

        gauge_result = await db.execute(text(gauge_query))
        gauges = {g.code: g for g in gauge_result.fetchall()}

        # Calculate flood risk for each zone
        zone_risks = []

        for zone in zones:
            # Basic risk calculation (simplified)
            base_risk = 0.1  # 10% base risk

            # Factor in nearby gauge levels
            gauge_risk = 0.0
            gauge_count = 0

            for gauge in gauges.values():
                if gauge.reading_value is not None:
                    if gauge.alert_threshold and gauge.reading_value >= gauge.alert_threshold:
                        gauge_risk += 0.8
                    elif gauge.warning_threshold and gauge.reading_value >= gauge.warning_threshold:
                        gauge_risk += 0.5
                    else:
                        # Risk based on percentage of warning threshold
                        if gauge.warning_threshold:
                            risk_factor = gauge.reading_value / gauge.warning_threshold
                            gauge_risk += min(risk_factor * 0.3, 0.3)

                    gauge_count += 1

            avg_gauge_risk = gauge_risk / max(gauge_count, 1)

            # Combine risk factors
            total_risk = min(base_risk + avg_gauge_risk, 1.0)

            # Determine risk category
            if total_risk >= 0.75:
                risk_category = "severe"
            elif total_risk >= 0.5:
                risk_category = "high"
            elif total_risk >= 0.35:
                risk_category = "moderate"
            else:
                risk_category = "low"

            # Generate risk drivers
            risk_drivers = []
            if avg_gauge_risk > 0.3:
                risk_drivers.append({
                    "factor": "river_levels",
                    "contribution": round(avg_gauge_risk, 2),
                    "description": "Elevated river gauge readings"
                })

            if zone.population > 10000:
                risk_drivers.append({
                    "factor": "population_density",
                    "contribution": 0.1,
                    "description": "High population density increases impact"
                })

            zone_risks.append({
                "zone_id": zone.code,
                "zone_name": zone.name,
                "risk_level": round(total_risk, 3),
                "risk_category": risk_category,
                "confidence": 0.75 if gauge_count > 0 else 0.4,
                "risk_drivers": risk_drivers,
                "affected_population": int(zone.population * total_risk),
                "time_horizon_hours": time_horizon,
                "recommended_actions": get_recommended_actions(risk_category),
                "geometry": zone.geometry
            })

        return {
            "zones": zone_risks,
            "metadata": {
                "time_horizon": time_horizon,
                "generated_at": datetime.utcnow(),
                "gauge_count": len(gauges),
                "data_quality": "good" if len(gauges) > 0 else "limited"
            }
        }

    except Exception as e:
        raise ValueError(f"Failed to generate flood risk predictions: {str(e)}")


def get_recommended_actions(risk_category: str) -> List[str]:
    """Get recommended actions based on risk category."""
    actions = {
        "severe": [
            "Activate emergency response protocols",
            "Evacuate high-risk areas",
            "Deploy emergency resources",
            "Issue public warnings"
        ],
        "high": [
            "Monitor conditions closely",
            "Prepare emergency resources",
            "Alert emergency services",
            "Consider precautionary evacuations"
        ],
        "moderate": [
            "Increase monitoring frequency",
            "Review emergency plans",
            "Alert relevant authorities",
            "Prepare resources for deployment"
        ],
        "low": [
            "Continue normal monitoring",
            "Review forecast updates",
            "Maintain situational awareness"
        ]
    }

    return actions.get(risk_category, actions["low"])
