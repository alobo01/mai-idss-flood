"""
FastAPI backend for flood prediction system
"""
import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from app.db import get_sqlalchemy_engine
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field


class SafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that safely handles special float values"""

    def default(self, obj):
        # Handle numpy types
        if isinstance(obj, np.generic):
            try:
                return obj.item()
            except (ValueError, OverflowError):
                return None

        # Handle pandas Timestamp
        if hasattr(obj, 'isoformat') and callable(obj.isoformat):
            return obj.isoformat()

        return super().default(obj)

    def encode(self, obj):
        # Override encode to handle special float values
        def _safe_floats(o):
            if isinstance(o, dict):
                return {k: _safe_floats(v) for k, v in o.items()}
            elif isinstance(o, list):
                return [_safe_floats(v) for v in o]
            elif isinstance(o, float):
                # Check for problematic float values
                if o != o:  # NaN
                    return None
                if o in (float('inf'), float('-inf')):  # Infinity
                    return None
                if not (-1e100 <= o <= 1e100):  # Out of reasonable range
                    return None
                return o
            else:
                return o

        return super().encode(_safe_floats(obj))


class SafeJSONResponse(JSONResponse):
    """Custom JSONResponse that uses SafeJSONEncoder"""

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=SafeJSONEncoder,
        ).encode("utf-8")

from .prediction.data_fetcher import DataFetcher
from .schemas import (
    PredictionResponse,
    Prediction,
    FloodRisk,
    Forecast,
    PredictionInterval,
    Allocation,
    AllocationMode,
    ImpactLevel,
    RuleScenario,
    DispatchRequest,
    DispatchPlanResponse,
    ResourceSummary,
    JobStatus,
    PredictAllRequest,
    ResourceCapacityUpdate,
    HealthResponse,
    ApiResponse,
    GeoJsonFeatureCollection,
    GeoJsonFeature,
    ResourceType,
    HistoricalPredictionResults,
    HistoricalPredictionSummary,
)
from .db import (
    get_all_zones,
    get_all_resource_types,
    get_last_30_days_raw_data,
    get_all_raw_data,
    get_last_raw_data_date,
    get_latest_prediction,
    get_prediction_history,
    get_prediction_history_with_actuals,
)
from .prediction_service import predict_next_days, predict_all_historical
from .rule_based import (
    RESOURCE_TYPES,
    build_dispatch_plan,
    build_zones_from_data,
    compute_pf_by_zone_from_global,
)
import os

# Repo root (three directories up from UI/backend/app)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# Use an environment-provided SCRIPTS_DIR if present (container-friendly), otherwise fall back to repo path
SCRIPTS_DIR = os.environ.get('SCRIPTS_DIR', os.path.join(REPO_ROOT, 'UI', 'scripts'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Flood Prediction API",
    description="Predicts Mississippi River levels at St. Louis for 1-3 days ahead",
    version="1.0.0",
    default_response_class=SafeJSONResponse
)

# Simple in-memory job store for background tasks
JOB_STORE: Dict[str, Dict[str, Any]] = {}
JOB_STORE_LOCK = threading.Lock()

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


def _safe_df_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert a pandas DataFrame into a JSON-serializable list of dicts, sanitizing
    values that are not JSON-friendly (NaN, inf, numpy types, datetime).
    - Replace +/-inf with None
    - Replace NaN/NA with None
    - Convert numpy scalars to Python primitives
    - Convert datetimes to ISO 8601 strings
    - Ensure all float values are within JSON-compliant range
    """
    if df is None:
        return []

    df2 = df.copy()

    # Replace infinities and NaN with None
    df2 = df2.replace([np.inf, -np.inf, np.nan], None)

    # Convert datetimes to ISO strings
    datetime_cols = []
    for col in df2.columns:
        if df2[col].dtype.kind in ['M', 'm']:  # datetime or timedelta
            datetime_cols.append(col)

    for col in datetime_cols:
        df2[col] = df2[col].apply(lambda x: x.isoformat() if x is not None and not pd.isna(x) else None)

    # Convert all values to JSON-safe Python types
    def _convert_value(x):
        """Convert individual values to JSON-safe types"""
        if x is None or pd.isna(x):
            return None

        # Handle numpy types
        if isinstance(x, np.generic):
            try:
                x = x.item()
            except (ValueError, OverflowError):
                return None

        # Handle float values - check for JSON compliance
        if isinstance(x, float):
            # JSON doesn't support NaN, inf, or very large/small numbers
            # Check for NaN and infinity
            if x != x:  # NaN check
                return None
            if x in (float('inf'), float('-inf')):
                return None
            # Check for reasonable range (JSON float limits)
            if not (-1e100 <= x <= 1e100):  # Use conservative range
                logger.warning(f"Float value {x} out of range, replacing with None")
                return None

        return x

    # Apply conversion to all values
    records = []
    for idx, (_, row) in enumerate(df2.iterrows()):
        converted_row = {}
        for key, value in row.items():
            try:
                converted_val = _convert_value(value)
                converted_row[str(key)] = converted_val
            except Exception as e:
                logger.warning(f"Error converting value at row {idx}, column {key}: {e}, value: {value}")
                converted_row[str(key)] = None
        records.append(converted_row)

    return records




@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint - API health check"""
    return ApiResponse(
        success=True,
        message="Flood Prediction API is running",
        data={
            "status": "healthy",
            "version": "1.0.0",
            "endpoints": {
                "predict": "/predict",
                "docs": "/docs"
            }
        }
    )

@app.get("/raw-data", response_model=ApiResponse)
async def raw_data():
    """Return the most recent 30 days of raw sensor data from the database."""
    data = get_last_30_days_raw_data()
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail="No raw data found")
    return ApiResponse(
        success=True,
        message="Raw data retrieved successfully",
        data={"rows": _safe_df_records(data)}
    )


@app.get("/raw-data/last-date", response_model=ApiResponse)
async def last_raw_data_date():
    """Return the date of the last row in the raw_data table."""
    last_date = get_last_raw_data_date()
    if last_date is None:
        raise HTTPException(status_code=404, detail="No raw data found")
    return ApiResponse(
        success=True,
        message="Last raw data date retrieved successfully",
        data={"last_date": last_date}
    )


@app.get("/prediction-history", response_model=ApiResponse)
async def prediction_history(limit: int = Query(90, ge=1, le=1000)):
    """Return recent stored predictions (all horizons) joined with observed values for comparison."""
    df = get_prediction_history_with_actuals(limit=limit)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No prediction history found")

    # Use python's built-in json to manually serialize and handle problematic values
    import json as pyjson

    # Convert DataFrame to a list of dictionaries and handle problematic values
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            # Handle problematic values
            if pd.isna(val) or val in (np.inf, -np.inf):
                record[col] = None
            elif isinstance(val, np.generic):
                try:
                    record[col] = val.item()
                except (ValueError, OverflowError):
                    record[col] = None
            elif isinstance(val, float):
                # Check for out-of-range values that can't be JSON serialized
                if not (-1e100 <= val <= 1e100):
                    record[col] = None
                else:
                    record[col] = val
            elif hasattr(val, 'isoformat'):  # datetime objects
                record[col] = val.isoformat()
            else:
                record[col] = val
        records.append(record)

    # Manually create JSON string
    json_data = pyjson.dumps({
        "success": True,
        "message": "Prediction history retrieved successfully",
        "data": {"rows": records}
    })

    # Return a plain response with manually serialized JSON
    from fastapi.responses import Response
    return Response(content=json_data, media_type="application/json")


@app.post("/predict-all", response_model=Union[JobStatus, HistoricalPredictionResults])
async def predict_all(
    lead_times: str = Query(
        "1,2,3",
        description="Comma-separated list of lead times in days (e.g., '1,2,3')"
    ),
    skip_cached: bool = Query(
        True,
        description="Skip dates that already have predictions cached"
    ),
    run_in_background: bool = Query(
        False,
        description="Run the prediction process in background (returns immediately with job ID)"
    )
):
    """
    Generate predictions for all available historical data points.

    This endpoint processes all historical data in the database and generates
    predictions for each valid 30-day window, providing a comprehensive backtest
    of the prediction models.

    Args:
        lead_times: Comma-separated list of lead times in days (default: "1,2,3")
        skip_cached: Skip dates that already have predictions cached (default: True)
        run_in_background: Run asynchronously in background (default: False)

    Returns:
        If run_in_background=False: Full prediction results
        If run_in_background=True: Job status with ID for checking progress
    """

    try:
        # Parse lead times
        try:
            lead_time_list = [int(x.strip()) for x in lead_times.split(',') if x.strip()]
            if not lead_time_list:
                lead_time_list = [1, 2, 3]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid lead_times format. Use comma-separated integers like '1,2,3'"
            )

        logger.info(f"Predict-all request received (lead_times={lead_time_list}, skip_cached={skip_cached}, run_in_background={run_in_background})")

        if run_in_background:
            # For now, run synchronously but could implement async job queue here
            # Return a job-like response immediately
            job_id = f"predict_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Start background process (in a real implementation, this would be a proper job queue)
            import threading
            def background_job():
                try:
                    # progress callback
                    def on_progress(pct):
                        with JOB_STORE_LOCK:
                            if JOB_STORE.get(job_id):
                                JOB_STORE[job_id].update({
                                    'percent': pct.get('percent'),
                                    'completed': pct.get('completed'),
                                    'total': pct.get('total'),
                                    'eta_seconds': pct.get('eta_seconds'),
                                    'message': pct.get('message'),
                                    'last_update': datetime.now().isoformat(),
                                })

                    with JOB_STORE_LOCK:
                        JOB_STORE[job_id].update({
                            'status': 'running',
                            'started_at': datetime.now().isoformat(),
                        })

                    def cancel_check():
                        with JOB_STORE_LOCK:
                            return bool(JOB_STORE.get(job_id, {}).get('cancel_requested', False))

                    result = predict_all_historical(lead_times=lead_time_list, skip_cached=skip_cached, on_progress=on_progress, cancel_check=cancel_check)

                    with JOB_STORE_LOCK:
                        JOB_STORE[job_id].update({
                            'status': 'completed',
                            'completed_at': datetime.now().isoformat(),
                            'result': result,
                            'percent': 100.0,
                        })

                    logger.info(f"Background job {job_id} completed: {result['total_predictions']} predictions")
                except Exception as e:
                    logger.error(f"Background job {job_id} failed: {e}", exc_info=True)
                    with JOB_STORE_LOCK:
                        JOB_STORE[job_id].update({
                            'status': 'failed',
                            'error': str(e),
                            'completed_at': datetime.now().isoformat(),
                        })

            # Initialize job store entry
            with JOB_STORE_LOCK:
                JOB_STORE[job_id] = {
                    'status': 'queued',
                    'job_id': job_id,
                    'percent': 0.0,
                    'completed': 0,
                    'total': None,
                    'eta_seconds': None,
                    'message': 'queued',
                    'created_at': datetime.now().isoformat(),
                }

            thread = threading.Thread(target=background_job)
            thread.daemon = True
            thread.start()

            return JobStatus(
                job_id=job_id,
                status="started",
                message="Historical prediction process started in background",
                created_at=datetime.now().isoformat(),
                lead_times=lead_time_list,
                skip_cached=skip_cached
            )
        else:
            # Run synchronously and return full results
            # Attach a no-op progress logger for compatibility
            def _log_progress(p):
                logger.info(f"Predict-all progress: {p}")

            def _no_cancel():
                return False

            results = predict_all_historical(lead_times=lead_time_list, skip_cached=skip_cached, on_progress=_log_progress, cancel_check=_no_cancel)

            # Convert the results to match the expected response model
            summary_dict = {}
            for key, value in results.get('summary', {}).items():
                if isinstance(value, dict):
                    summary_dict[key] = HistoricalPredictionSummary(**value)
                else:
                    summary_dict[key] = value

            predictions_by_lead_time = {}
            for lead, preds in results.get('predictions_by_lead_time', {}).items():
                predictions_by_lead_time[lead] = [Prediction(**p) for p in preds]

            return HistoricalPredictionResults(
                status="completed",
                timestamp=datetime.now().isoformat(),
                lead_times=lead_time_list,
                total_predictions=results.get('total_predictions', 0),
                predictions_by_lead_time=predictions_by_lead_time,
                skipped_cached=results.get('skipped_cached', 0),
                errors=results.get('errors', []),
                summary=summary_dict,
                cancelled=results.get('summary', {}).get('cancelled', False)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predict-all failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Predict-all failed: {str(e)}"
        )


@app.get("/predict-all/status/{job_id}", response_model=JobStatus)
async def predict_all_status(job_id: str):
    """Return status for a background predict-all job"""
    with JOB_STORE_LOCK:
        job = JOB_STORE.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobStatus(**job)


@app.post("/predict-all/cancel/{job_id}")
async def predict_all_cancel(job_id: str):
    """Request cancellation for a running background job (best-effort)."""
    # This signal simply marks job as 'cancel_requested' and the worker
    # should cooperatively check and stop. predict_all_historical is not
    # currently cooperative, so this is a soft cancel for now.
    with JOB_STORE_LOCK:
        job = JOB_STORE.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.get('status') not in ('running', 'started'):
            return {"status": job.get('status'), "message": "Job not running"}
        job['cancel_requested'] = True
        job['message'] = 'cancel requested'
        return {"status": "cancel_requested", "job_id": job_id}


@app.get('/scripts/predict-all/available')
async def script_predict_all_available():
        """Check for the existence of the scripts/predict_all.py script on disk."""
        script_path = os.path.join(SCRIPTS_DIR, 'predict_all.py')
        return {"available": os.path.exists(script_path)}


@app.get('/scripts/predict-all/status')
async def script_predict_all_status():
        """Serve the last status JSON file from the script if present."""
        status_file = os.path.join(SCRIPTS_DIR, 'predict_all_status.json')
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail='No status file found')
        try:
            with open(status_file, 'r') as fh:
                data = fh.read()
            return json.loads(data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/rule-based/dispatch", response_model=DispatchPlanResponse)
async def rule_based_dispatch(
    total_units: int = Query(20, ge=1, le=200, description="Total deployable response units"),
    mode: AllocationMode = Query(
        AllocationMode.FUZZY,
        description="Allocation mode used by the rule-based planner",
    ),
    lead_time: int = Query(1, ge=1, le=7, description="Lead time (days ahead) for the cached prediction"),
    scenario: RuleScenario = Query(
        RuleScenario.NORMAL,
        description="Which scenario (best/normal/worst) determines the interval level used by the rule-based planner",
    ),
    global_pf: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Optional override for global flood probability (0-1). If provided, uses this instead of cached prediction.",
    ),
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
    def _resolve_prediction_from_cached(prediction: Dict[str, Any], scenario_value: RuleScenario) -> Tuple[float, str, float]:
        def _to_float(val: Any, default: float = 0.0) -> float:
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        median_level = prediction.get("predicted_level")
        lower_bound = prediction.get("lower_bound_80")
        upper_bound = prediction.get("upper_bound_80")

        selected_level = median_level
        source = "median"

        if scenario_value == RuleScenario.BEST and lower_bound is not None:
            selected_level = lower_bound
            source = "prediction_interval_lower"
        elif scenario_value == RuleScenario.WORST and upper_bound is not None:
            selected_level = upper_bound
            source = "prediction_interval_upper"

        if selected_level is None:
            if median_level is not None:
                selected_level = median_level
                source = "median"
            elif lower_bound is not None:
                selected_level = lower_bound
                source = "prediction_interval_lower"
            elif upper_bound is not None:
                selected_level = upper_bound
                source = "prediction_interval_upper"
            else:
                selected_level = 0.0
                source = "fallback"

        probability = max(0.0, min(1.0, _to_float(prediction.get("flood_probability"), 0.0)))
        return _to_float(selected_level, 0.0), source, probability

    last_prediction_summary: Optional[Dict[str, Any]] = None
    latest = get_latest_prediction(days_ahead=lead_time)

    # Use explicit override if provided
    if global_pf is not None:
        try:
            global_pf = float(global_pf)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid global_pf value")
        global_pf = max(0.0, min(1.0, global_pf))
    else:
        # If there's no cached prediction for this lead time, attempt to generate
        # one by running the prediction pipeline on the last 30 days of data.
        if latest is None:
            logger.info("No cached prediction for %s-day horizon; attempting to generate one", lead_time)
            raw_data = get_last_30_days_raw_data()
            if raw_data is None or len(raw_data) < 30:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"No cached prediction found for the {lead_time}-day horizon and insufficient raw data to generate prediction "
                        f"(need 30 days). Provide `global_pf` override or populate predictions."
                    ),
                )

            # Generate prediction(s) for requested lead time and cache them
            try:
                preds = predict_next_days(raw_data, lead_times=[lead_time])
                logger.info("Generated predictions for lead_time=%s: %s", lead_time, preds)
            except Exception as e:
                logger.error("Failed to generate predictions on-the-fly: %s", e)
                raise HTTPException(status_code=500, detail=f"Failed to generate prediction: {e}")

            # Re-fetch latest after generation
            latest = get_latest_prediction(days_ahead=lead_time)

        if latest is None:
            # If still missing, fail explicitly
            raise HTTPException(
                status_code=404,
                detail=f"No cached prediction available for the {lead_time}-day horizon",
            )

        selected_level, level_source, selected_probability = _resolve_prediction_from_cached(latest, scenario)
        global_pf = max(0.0, min(1.0, selected_probability))
        last_prediction_summary = {
            **latest,
            "scenario": scenario.value,
            "selected_level": selected_level,
            "selected_level_source": level_source,
            "selected_probability": selected_probability,
        }
        logger.debug(
            "Rule-based dispatch scenario=%s used level=%.2f (%s) with pf=%.3f",
            scenario.value,
            selected_level,
            level_source,
            selected_probability,
        )

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
    # Force fuzzy heuristic allocation regardless of the `mode` query param.
    # The optimizer path (`use_optimizer=True`) is still respected.
    forced_mode = "fuzzy"
    logger.info("Forcing allocation mode to fuzzy (overriding mode=%s)", mode)

    dispatch = build_dispatch_plan(
        zones,
        total_units=total_units,
        mode=forced_mode,
        max_units_per_zone=max_units_per_zone,
        use_optimizer=use_optimizer,
        resource_capacities=resource_capacities,
    )

    # Convert dispatch allocations to Allocation models
    allocation_models = []
    for allocation in dispatch:
        zone_id = allocation.get("zone_id")
        if not isinstance(zone_id, str):
            continue

        impact = allocation.get("impact_level")
        impact_key = impact if isinstance(impact, str) else ""
        impact_color = IMPACT_COLOR_MAP.get(impact_key, DEFAULT_IMPACT_COLOR)

        pf_val = round(pf_by_zone.get(zone_id, 0.0), 4)
        zone_meta = zone_lookup.get(zone_id)
        vulnerability = round(zone_meta.vulnerability, 3) if zone_meta else None
        is_critical_infra = zone_meta.is_critical_infra if zone_meta else None

        # Impact factor (iz) = pf * vulnerability
        try:
            vuln_val = float(vulnerability or 0.0)
            impact_factor = round(pf_val * vuln_val, 4)
        except Exception:
            impact_factor = None

        # Simple vulnerability category: LOW / MEDIUM / HIGH
        def _vuln_category(v: Optional[float]) -> Optional[str]:
            if v is None:
                return None
            if v < 0.33:
                return "LOW"
            if v < 0.66:
                return "MEDIUM"
            return "HIGH"

        vulnerability_category = _vuln_category(vulnerability)

        allocation_model = Allocation(
            zone_id=zone_id,
            zone_name=allocation.get("zone_name", ""),
            impact_level=ImpactLevel(allocation.get("impact_level", "NORMAL")),
            impact_color=impact_color,
            allocation_mode=AllocationMode(allocation.get("allocation_mode", "fuzzy").lower()),
            units_allocated=allocation.get("units_allocated", 0),
            max_units_per_zone=max_units_per_zone,
            priority_index=allocation.get("priority_index"),
            resource_priority=allocation.get("resource_priority", []),
            resource_units=allocation.get("resource_units", {}),
            resource_scores=allocation.get("resource_scores", {}),
            pf=pf_val,
            vulnerability=vulnerability,
            vulnerability_category=vulnerability_category,
            category=vulnerability_category,
            is_critical_infra=is_critical_infra,
            impact_factor=impact_factor,
            satisfaction_level=allocation.get("satisfaction_level"),
            fairness_level=allocation.get("fairness_level")
        )
        allocation_models.append(allocation_model)

    aggregated_resources = _aggregate_resource_units(dispatch)
    total_allocated_units = sum(zone.get("units_allocated", 0) for zone in dispatch)

    # Get resource type metadata
    resource_metadata_raw = get_all_resource_types()
    resource_metadata = {r["resource_id"]: ResourceType(**r) for r in resource_metadata_raw}

    # Extract fairness level if using optimizer
    fairness_level = None
    if use_optimizer and dispatch:
        fairness_level = dispatch[0].get("fairness_level")

    # Check whether the fuzzy engine (simpful) is available for real fuzzy resource priorities
    try:
        from .rule_based import allocations as _allocs
        fuzzy_engine_available = bool(getattr(_allocs, "_HAS_SIMPFUL", False))
    except Exception:
        fuzzy_engine_available = False

    return DispatchPlanResponse(
        lead_time_days=lead_time,
        mode=forced_mode,
        fuzzy_engine_available=fuzzy_engine_available,
        use_optimizer=use_optimizer,
        total_units=total_units if not use_optimizer else total_allocated_units,
        max_units_per_zone=max_units_per_zone,
        global_flood_probability=global_pf,
        scenario=scenario,
        last_prediction=last_prediction_summary or latest,
        resource_summary=ResourceSummary(
            total_allocated_units=total_allocated_units,
            per_resource_type=aggregated_resources,
            available_capacity=resource_capacities if use_optimizer else None
        ),
        fairness_level=fairness_level,
        resource_metadata=resource_metadata,
        impact_color_map=IMPACT_COLOR_MAP,
        zones=allocation_models
    )


@app.get("/zones", response_model=ApiResponse)
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
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine)
        return ApiResponse(
            success=True,
            message="Zones retrieved successfully",
            data={"rows": _safe_df_records(df)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load zones: {e}")


@app.get("/resource-types", response_model=ApiResponse)
async def resource_types():
    """
    Return all available resource types with metadata (name, description, icon).
    """
    try:
        resources = get_all_resource_types()
        if not resources:
            raise HTTPException(status_code=404, detail="No resource types found")
        return ApiResponse(
            success=True,
            message="Resource types retrieved successfully",
            data={"rows": resources}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load resource types: {e}")




@app.put("/resource-types/capacities", response_model=ApiResponse)
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
        return ApiResponse(
            success=True,
            message=f"Updated {updated_count} resource capacities",
            data={
                "updated_count": updated_count,
                "resources": resources
            }
        )
    except Exception as e:
        logger.error(f"Failed to update resource capacities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update capacities: {e}")


@app.get("/gauges", response_model=ApiResponse)
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
    return ApiResponse(
        success=True,
        message="Gauges retrieved successfully",
        data={"rows": gauges}
    )


@app.get("/zones-geo", response_model=GeoJsonFeatureCollection)
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
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine)

        features = []
        for _, row in df.iterrows():
            geo = row["geojson"]
            if isinstance(geo, str):
                geo = json.loads(geo)
            # Normalize to Feature shape
            feature = GeoJsonFeature(
                geometry=geo.get("geometry", geo if isinstance(geo, dict) else {}),
                properties={
                    "zone_id": row["zone_id"],
                    "name": row["name"],
                    "river_proximity": float(row["river_proximity"]) if row["river_proximity"] is not None else None,
                    "elevation_risk": float(row["elevation_risk"]) if row["elevation_risk"] is not None else None,
                    "pop_density": float(row["pop_density"]) if row["pop_density"] is not None else None,
                    "crit_infra_score": float(row["crit_infra_score"]) if row["crit_infra_score"] is not None else None,
                    "hospital_count": int(row["hospital_count"]) if row["hospital_count"] is not None else None,
                    "critical_infra": bool(row["critical_infra"]) if row["critical_infra"] is not None else False,
                },
            )
            features.append(feature)

        return GeoJsonFeatureCollection(features=features)
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
        
        # Generate predictions for 1, 2, and 3 days (now returns Pydantic models directly)
        predictions = predict_next_days(raw_data, lead_times=[1, 2, 3])

        logger.info(f"Successfully generated {len(predictions)} predictions")

        # Build response - convert Pydantic models to dicts for JSON serialization
        response = PredictionResponse(
            timestamp=datetime.now().isoformat(),
            use_real_time_api=use_real_time_api,
            data_source=data_source,
            predictions=[pred.model_dump() for pred in predictions]
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


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    try:
        # Try to connect to database
        from .db import test_connection
        db_healthy = test_connection()

        status = "healthy" if db_healthy else "degraded"
        db_status = "connected" if db_healthy else "disconnected"

        return HealthResponse(
            status=status,
            database=db_status,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )
