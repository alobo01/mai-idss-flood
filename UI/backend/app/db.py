"""
Database connection and query utilities
"""
import os
import psycopg2
import pandas as pd
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5439')),
    'database': os.getenv('DB_NAME', 'flood_prediction'),
    'user': os.getenv('DB_USER', 'flood_user'),
    'password': os.getenv('DB_PASSWORD', 'flood_password')
}


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
        conn = get_connection()
        
        # Read into DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Reverse order (oldest first)
        df = df.iloc[::-1].reset_index(drop=True)
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        logger.info(f"Retrieved {len(df)} days from database")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch raw data: {e}")
        return None


def insert_prediction(forecast_date: str, predicted_level: float, flood_probability: float, days_ahead: int = 1,
                      lower_bound_80: Optional[float] = None, upper_bound_80: Optional[float] = None,
                      model_version: Optional[str] = None, model_type: Optional[str] = None):
    """
    Insert or update prediction in database
    
    Args:
        date: Prediction date (YYYY-MM-DD)
        predicted_level: Predicted river level in feet
        flood_probability: Probability of flooding (0-1)
    """
    
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
            predicted_level,
            lower_bound_80,
            upper_bound_80,
            flood_probability,
            model_version,
            model_type,
            forecast_date,
            days_ahead,
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
                forecast_date,
                days_ahead,
                model_version,
                predicted_level,
                lower_bound_80,
                upper_bound_80,
                flood_probability,
                model_type,
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
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
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
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
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
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=(forecast_date, days_ahead))
        conn.close()

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
        clauses.append("lead_time_days = %s")
        params.append(days_ahead)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ''
    query = f"""
        SELECT forecast_date, lead_time_days, predicted_level, lower_bound_80, upper_bound_80, flood_probability, model_version, model_type, created_at
        FROM predictions
        {where_clause}
        ORDER BY created_at DESC
        LIMIT 1
    """

    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=tuple(params) if params else None)
        conn.close()

        if df.empty:
            return None

        row = df.iloc[0]
        return {
            'forecast_date': str(row['forecast_date']),
            'date': str(row['forecast_date']),
            'predicted_level': float(row['predicted_level']) if row.get('predicted_level') is not None else None,
            'lower_bound_80': float(row['lower_bound_80']) if row.get('lower_bound_80') is not None else None,
            'upper_bound_80': float(row['upper_bound_80']) if row.get('upper_bound_80') is not None else None,
            'flood_probability': float(row['flood_probability']) if row.get('flood_probability') is not None else None,
            'days_ahead': int(row['lead_time_days']) if row.get('lead_time_days') is not None else None,
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
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
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
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
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
