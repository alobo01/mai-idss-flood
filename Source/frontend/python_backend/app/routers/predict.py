"""Prediction endpoints for river levels and flood risk."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
# import numpy as np  # Temporarily disabled for deployment

from ..database import get_db
from ..schemas import RiverLevelPrediction, FloodRiskPrediction, ErrorResponse

router = APIRouter()


@router.get("/predict/river-level", response_model=List[RiverLevelPrediction], tags=["Predictions"])
async def predict_river_level(
    gauge_code: Optional[str] = Query(None, description="Gauge code to predict for"),
    horizon: int = Query(24, ge=1, le=168, description="Prediction horizon in hours"),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict river levels for specified gauge(s).

    Uses historical data and simple linear regression for prediction.
    In production, this would integrate with ML models.
    """
    try:
        # Build query for recent gauge readings
        gauge_filter = ""
        params = {"horizon_hours": horizon}

        if gauge_code:
            gauge_filter = "WHERE g.code = :gauge_code"
            params["gauge_code"] = gauge_code

        # Get recent readings for trend analysis
        query = f"""
            WITH recent_readings AS (
                SELECT
                    g.id as gauge_id,
                    g.code,
                    g.name,
                    g.alert_threshold,
                    g.warning_threshold,
                    g.river_name,
                    gr.reading_value,
                    gr.reading_time,
                    ROW_NUMBER() OVER (PARTITION BY g.id ORDER BY gr.reading_time DESC) as rn
                FROM gauges g
                LEFT JOIN gauge_readings gr ON gr.gauge_id = g.id
                    AND gr.reading_time >= NOW() - INTERVAL '72 hours'
                    AND gr.quality_flag = 'good'
                {gauge_filter}
            )
            SELECT
                gauge_id,
                code,
                name,
                alert_threshold,
                warning_threshold,
                river_name,
                reading_value,
                reading_time,
                rn
            FROM recent_readings
            WHERE rn <= 72
            ORDER BY code, rn
        """

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        if not rows:
            return []

        # Group readings by gauge
        gauge_data = {}
        for row in rows:
            if row.code not in gauge_data:
                gauge_data[row.code] = {
                    'name': row.name,
                    'river_name': row.river_name,
                    'alert_threshold': row.alert_threshold,
                    'warning_threshold': row.warning_threshold,
                    'readings': []
                }

            if row.reading_value is not None:
                gauge_data[row.code]['readings'].append({
                    'value': float(row.reading_value),
                    'time': row.reading_time
                })

        predictions = []

        # Generate predictions for each gauge
        for gauge_code, data in gauge_data.items():
            readings = data['readings']

            if len(readings) < 2:
                # Not enough data for prediction, use current value
                current_value = readings[0]['value'] if readings else 0.0
                trend = 0.0
            else:
                # Simple linear regression for trend
                times = [(r['time'] - readings[0]['time']).total_seconds() / 3600.0 for r in readings]
                values = [r['value'] for r in readings]

                if len(times) > 1:
                    # Calculate trend (slope)
                    n = len(times)
                    sum_x = sum(times)
                    sum_y = sum(values)
                    sum_xy = sum(t * v for t, v in zip(times, values))
                    sum_x2 = sum(t * t for t in times)

                    trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if n * sum_x2 != sum_x * sum_x else 0.0
                else:
                    trend = 0.0

                current_value = values[-1] if values else 0.0

            # Generate hourly predictions
            for hour in range(1, horizon + 1):
                predicted_value = max(0, current_value + (trend * hour))
                prediction_time = datetime.utcnow() + timedelta(hours=hour)

                # Determine confidence based on data availability and trend
                confidence = 0.9 if len(readings) >= 24 else 0.7 if len(readings) >= 12 else 0.5

                # Determine risk level
                risk_level = "low"
                if data['alert_threshold'] and predicted_value >= data['alert_threshold']:
                    risk_level = "severe"
                elif data['warning_threshold'] and predicted_value >= data['warning_threshold']:
                    risk_level = "moderate"
                elif predicted_value > current_value * 1.1:  # 10% increase
                    risk_level = "moderate"

                predictions.append(RiverLevelPrediction(
                    gauge_id=gauge_code,
                    gauge_name=data['name'],
                    river_name=data['river_name'],
                    prediction_time=prediction_time,
                    predicted_level=round(predicted_value, 2),
                    confidence_level=confidence,
                    risk_level=risk_level,
                    trend_per_hour=round(trend, 3),
                    data_points_used=len(readings)
                ))

        return predictions

    except Exception as e:
        raise ValueError(f"Failed to generate river level predictions: {str(e)}")


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