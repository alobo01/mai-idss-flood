"""
Database connection and query utilities
"""
import os
import psycopg2
import pandas as pd
from typing import Optional, Any, Dict, List
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .schemas import (
    RawDataRecord,
    ZoneMetadata,
    ResourceType,
    PredictionRecord,
)
from .db_models import (
    DatabaseQueryParams,
    PredictionInsert,
    PredictionUpdate,
    ZoneInsert,
    ZoneUpdate,
    ResourceTypeInsert,
    ResourceTypeUpdate,
    RawDataInsert,
    PredictionDAO,
    ZoneDAO,
    ResourceTypeDAO,
    RawDataDAO,
)

logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5439')),
    'database': os.getenv('DB_NAME', 'flood_prediction'),
    'user': os.getenv('DB_USER', 'flood_user'),
    'password': os.getenv('DB_PASSWORD', 'flood_password')
}

# Global SQLAlchemy engine variable
_engine: Optional[Engine] = None

def get_sqlalchemy_engine() -> Engine:
    """
    Create or return SQLAlchemy engine for database connections

    Returns:
        SQLAlchemy engine object
    """
    global _engine
    if _engine is None:
        # Create database URL from config
        db_url = (
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Set to True for SQL logging in development
        )
        logger.info("Created SQLAlchemy engine")
    return _engine


def get_connection():
    """
    Create database connection
    
    Returns:
        psycopg2 connection object
    
    Raises:
        Exception: If connection fails
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        conn = get_connection()
        conn.close()
        return True
    except:
        return False


def get_last_30_days_raw_data() -> Optional[pd.DataFrame]:
    """
    Fetch last 30 days of raw data from database

    Returns:
        DataFrame with columns matching the schema:
        - date
        - daily_precip
        - daily_temp_avg
        - daily_snowfall
        - daily_humidity
        - daily_wind
        - soil_deep_30d
        - target_level_max
        - hermann_level
        - grafton_level

        Returns None if query fails
    """

    query = """
        SELECT
            date,
            daily_precip,
            daily_temp_avg,
            daily_snowfall,
            daily_humidity,
            daily_wind,
            soil_deep_30d,
            target_level_max,
            hermann_level,
            grafton_level
        FROM raw_data
        ORDER BY date DESC
        LIMIT 30
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()

        # Read into DataFrame
        df = pd.read_sql_query(query, engine)

        # Reverse order (oldest first)
        df = df.iloc[::-1].reset_index(drop=True)

        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])

        logger.info(f"Retrieved {len(df)} days from database")

        return df

    except Exception as e:
        logger.error(f"Failed to fetch raw data: {e}")
        return None


def get_all_raw_data() -> Optional[pd.DataFrame]:
    """
    Fetch all available raw data from database

    Returns:
        DataFrame with columns matching the schema:
        - date
        - daily_precip
        - daily_temp_avg
        - daily_snowfall
        - daily_humidity
        - daily_wind
        - soil_deep_30d
        - target_level_max
        - hermann_level
        - grafton_level

        Returns None if query fails
    """

    query = """
        SELECT
            date,
            daily_precip,
            daily_temp_avg,
            daily_snowfall,
            daily_humidity,
            daily_wind,
            soil_deep_30d,
            target_level_max,
            hermann_level,
            grafton_level
        FROM raw_data
        ORDER BY date ASC
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()

        # Read into DataFrame
        df = pd.read_sql_query(query, engine)

        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])

        logger.info(f"Retrieved {len(df)} days of all historical data from database")

        return df

    except Exception as e:
        logger.error(f"Failed to fetch all raw data: {e}")
        return None


def insert_prediction(forecast_date: str, predicted_level: float, flood_probability: float, days_ahead: int = 1,
                      lower_bound_80: Optional[float] = None, upper_bound_80: Optional[float] = None,
                      model_version: Optional[str] = None, model_type: Optional[str] = None) -> None:
    """
    Insert or update prediction in database with type safety.

    Args:
        forecast_date: Prediction date (YYYY-MM-DD)
        predicted_level: Predicted river level in feet
        flood_probability: Probability of flooding (0-1)
        days_ahead: Days ahead for prediction
        lower_bound_80: Lower bound of 80% prediction interval
        upper_bound_80: Upper bound of 80% prediction interval
        model_version: Model version identifier
        model_type: Model type (xgboost, bayesian, lstm)
    """

    # Use Pydantic model for validation
    prediction_insert = PredictionInsert(
        forecast_date=forecast_date,
        predicted_level=predicted_level,
        flood_probability=flood_probability,
        days_ahead=days_ahead,
        lower_bound_80=lower_bound_80,
        upper_bound_80=upper_bound_80,
        model_version=model_version,
        model_type=model_type
    )

    # Use update-then-insert pattern to avoid relying on an ON CONFLICT
    # unique constraint. This safely upserts the prediction row.
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # The schema uses `date` and `days_ahead` as column names (see
        # UI/database/init/01-schema.sql). Use those column names in SQL but
        # return both `date` and `forecast_date` keys for compatibility.
        update_q = """
            UPDATE predictions
            SET predicted_level = %s,
                lower_bound_80 = %s,
                upper_bound_80 = %s,
                flood_probability = %s,
                model_version = %s,
                model_type = %s,
                created_at = CURRENT_TIMESTAMP
            WHERE date = %s AND days_ahead = %s
        """

        cursor.execute(update_q, (
            prediction_insert.predicted_level,
            prediction_insert.lower_bound_80,
            prediction_insert.upper_bound_80,
            prediction_insert.flood_probability,
            prediction_insert.model_version,
            prediction_insert.model_type,
            prediction_insert.forecast_date,
            prediction_insert.days_ahead,
        ))

        if cursor.rowcount == 0:
            insert_q = """
                INSERT INTO predictions (
                    date, days_ahead, model_version,
                    predicted_level, lower_bound_80, upper_bound_80,
                    flood_probability, model_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_q, (
                prediction_insert.forecast_date,
                prediction_insert.days_ahead,
                prediction_insert.model_version,
                prediction_insert.predicted_level,
                prediction_insert.lower_bound_80,
                prediction_insert.upper_bound_80,
                prediction_insert.flood_probability,
                prediction_insert.model_type,
            ))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Upserted prediction for {forecast_date} (days_ahead={days_ahead})")
    except Exception as e:
        logger.error(f"Failed to insert prediction: {e}")
        raise


def get_prediction_history(limit: int = 90) -> pd.DataFrame | None:
    """
    Return recent predictions from the database for all horizons.
    """
    query = """
        SELECT forecast_date, lead_time_days, predicted_level, lower_bound_80, upper_bound_80,
               flood_probability, model_version, model_type, created_at
        FROM predictions
        ORDER BY created_at DESC
        LIMIT %s
    """
    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine, params=(limit,))
        return df
    except Exception as e:
        logger.error(f"Failed to fetch prediction history: {e}")
        return None


def get_prediction_history_with_actuals(limit: int = 90) -> pd.DataFrame | None:
    """
    Return recent predictions joined with actual observed values (from raw_data).

    The result includes:
      - forecast_date
      - lead_time_days
      - predicted_level
      - lower_bound_80
      - upper_bound_80
      - flood_probability
      - actual_level (target_level_max from raw_data for the forecast_date)
      - model_version, model_type, created_at
    """
    # Use actual schema column names (`date`, `days_ahead`) but return
    # a column named `forecast_date` for compatibility with callers.
    query = """
        SELECT
            p.date AS forecast_date,
            p.days_ahead AS lead_time_days,
            p.predicted_level,
            p.lower_bound_80,
            p.upper_bound_80,
            p.flood_probability,
            rd.target_level_max AS actual_level,
            p.model_version,
            p.model_type,
            p.created_at
        FROM predictions p
        LEFT JOIN raw_data rd ON rd.date = p.date
        ORDER BY p.created_at DESC
        LIMIT %s
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine, params=(limit,))
        return df
    except Exception as e:
        logger.error(f"Failed to fetch prediction history with actuals: {e}")
        return None

def get_prediction(forecast_date: str, days_ahead: int) -> Optional[dict]:
    """Retrieve cached prediction for a given forecast_date and lead time.

    Note: the underlying table uses column `date` and `days_ahead`.
    This function accepts `forecast_date`/`days_ahead` as parameters but
    queries the actual columns and returns both `date` and
    `forecast_date` keys for compatibility.
    """
    query = """
        SELECT predicted_level, lower_bound_80, upper_bound_80, flood_probability, days_ahead, created_at, date
        FROM predictions
        WHERE date = %s AND days_ahead = %s
        LIMIT 1
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine, params=(forecast_date, days_ahead))

        if df.empty:
            return None

        row = df.iloc[0]
        # Provide both names to callers: `date` and `forecast_date`, and
        # `days_ahead` and `lead_time_days` where useful.
        return {
            'predicted_level': float(row['predicted_level']) if row.get('predicted_level') is not None else None,
            'lower_bound_80': float(row['lower_bound_80']) if row.get('lower_bound_80') is not None else None,
            'upper_bound_80': float(row['upper_bound_80']) if row.get('upper_bound_80') is not None else None,
            'flood_probability': float(row['flood_probability']) if row.get('flood_probability') is not None else None,
            'days_ahead': int(row['days_ahead']) if row.get('days_ahead') is not None else None,
            'lead_time_days': int(row['days_ahead']) if row.get('days_ahead') is not None else None,
            'date': str(row['date']) if row.get('date') is not None else None,
            'forecast_date': str(row['date']) if row.get('date') is not None else None,
            'created_at': row['created_at']
        }
    except Exception as e:
        logger.error(f"Failed to read cached prediction: {e}")
        return None


def get_latest_prediction(days_ahead: Optional[int] = None) -> Optional[dict]:
    """Return the most recent prediction record (optionally filtered by lead time)."""
    clauses = []
    params = []
    if days_ahead is not None:
        clauses.append("days_ahead = %s")
        params.append(days_ahead)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ''
    query = f"""
        SELECT date, days_ahead, predicted_level, lower_bound_80, upper_bound_80, flood_probability, model_version, model_type, created_at
        FROM predictions
        {where_clause}
        ORDER BY created_at DESC
        LIMIT 1
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine, params=tuple(params) if params else None)

        if df.empty:
            return None

        row = df.iloc[0]
        return {
            'forecast_date': str(row['date']),
            'date': str(row['date']),
            'predicted_level': float(row['predicted_level']) if row.get('predicted_level') is not None else None,
            'lower_bound_80': float(row['lower_bound_80']) if row.get('lower_bound_80') is not None else None,
            'upper_bound_80': float(row['upper_bound_80']) if row.get('upper_bound_80') is not None else None,
            'flood_probability': float(row['flood_probability']) if row.get('flood_probability') is not None else None,
            'days_ahead': int(row['days_ahead']) if row.get('days_ahead') is not None else None,
            'model_version': row.get('model_version'),
            'model_type': row.get('model_type'),
            'created_at': row['created_at']
        }
    except Exception as e:
        logger.error(f"Failed to fetch latest prediction: {e}")
        return None


def get_all_zones() -> List[Dict[str, Any]]:
    """Fetch zone metadata from the database."""
    query = """
        SELECT
            zone_id,
            name,
            river_proximity,
            elevation_risk,
            pop_density,
            crit_infra_score,
            hospital_count,
            critical_infra
        FROM zones
        ORDER BY zone_id
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine)
        if df.empty:
            return []
        df = df.fillna({
            'river_proximity': 0.0,
            'elevation_risk': 0.0,
            'pop_density': 0.0,
            'crit_infra_score': 0.0,
            'hospital_count': 0,
            'critical_infra': False,
        })
        records = df.to_dict(orient="records")
        normalized = []
        for row in records:
            normalized.append({str(k): v for k, v in row.items()})
        return normalized
    except Exception as e:
        logger.error(f"Failed to fetch zones: {e}")
        return []


def get_all_resource_types() -> List[Dict[str, Any]]:
    """Fetch all resource types from the database."""
    query = """
        SELECT
            resource_id,
            name,
            description,
            icon,
            display_order,
            capacity
        FROM resource_types
        ORDER BY display_order
    """

    try:
        # Use SQLAlchemy engine to avoid pandas warning
        engine = get_sqlalchemy_engine()
        df = pd.read_sql_query(query, engine)
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        normalized = []
        for row in records:
            normalized.append({str(k): v for k, v in row.items()})
        return normalized
    except Exception as e:
        logger.error(f"Failed to fetch resource types: {e}")
        return []


def get_all_resource_types_typed() -> List[ResourceType]:
    """Fetch all resource types from the database with type safety."""
    try:
        resource_dicts = get_all_resource_types()
        return [ResourceTypeDAO.to_schema(record) for record in resource_dicts]
    except Exception as e:
        logger.error(f"Failed to fetch typed resource types: {e}")
        return []


def insert_zone(zone: ZoneInsert) -> bool:
    """Insert a new zone into the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO zones (
                zone_id, name, river_proximity, elevation_risk, pop_density,
                crit_infra_score, hospital_count, critical_infra
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            zone.zone_id,
            zone.name,
            zone.river_proximity,
            zone.elevation_risk,
            zone.pop_density,
            zone.crit_infra_score,
            zone.hospital_count,
            zone.critical_infra
        ))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Inserted zone: {zone.zone_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert zone: {e}")
        return False


def insert_resource_type(resource: ResourceTypeInsert) -> bool:
    """Insert a new resource type into the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO resource_types (
                resource_id, name, description, icon, display_order, capacity
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            resource.resource_id,
            resource.name,
            resource.description,
            resource.icon,
            resource.display_order,
            resource.capacity
        ))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Inserted resource type: {resource.resource_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert resource type: {e}")
        return False


def insert_raw_data_batch(records: List[RawDataInsert]) -> int:
    """Insert multiple raw data records in a batch."""
    if not records:
        return 0

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO raw_data (
                date, daily_precip, daily_temp_avg, daily_snowfall,
                daily_humidity, daily_wind, soil_deep_30d,
                target_level_max, hermann_level, grafton_level
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                daily_precip = EXCLUDED.daily_precip,
                daily_temp_avg = EXCLUDED.daily_temp_avg,
                daily_snowfall = EXCLUDED.daily_snowfall,
                daily_humidity = EXCLUDED.daily_humidity,
                daily_wind = EXCLUDED.daily_wind,
                soil_deep_30d = EXCLUDED.soil_deep_30d,
                target_level_max = EXCLUDED.target_level_max,
                hermann_level = EXCLUDED.hermann_level,
                grafton_level = EXCLUDED.grafton_level
        """

        values = [
            (
                record.date, record.daily_precip, record.daily_temp_avg,
                record.daily_snowfall, record.daily_humidity, record.daily_wind,
                record.soil_deep_30d, record.target_level_max,
                record.hermann_level, record.grafton_level
            )
            for record in records
        ]

        cursor.executemany(query, values)
        inserted_count = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Inserted/updated {inserted_count} raw data records")
        return inserted_count
    except Exception as e:
        logger.error(f"Failed to insert raw data batch: {e}")
        return 0
