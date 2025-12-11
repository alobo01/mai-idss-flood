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


def insert_prediction(date: str, predicted_level: float, flood_probability: float, days_ahead: int = 1):
    """
    Insert or update prediction in database
    
    Args:
        date: Prediction date (YYYY-MM-DD)
        predicted_level: Predicted river level in feet
        flood_probability: Probability of flooding (0-1)
    """
    
    query = """
        INSERT INTO predictions (date, predicted_level, flood_probability, days_ahead)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (date, days_ahead) 
        DO UPDATE SET
            predicted_level = EXCLUDED.predicted_level,
            flood_probability = EXCLUDED.flood_probability,
            created_at = CURRENT_TIMESTAMP
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, (date, predicted_level, flood_probability, days_ahead))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Inserted prediction for {date}")
        
    except Exception as e:
        logger.error(f"Failed to insert prediction: {e}")
        raise


def get_prediction_history(limit: int = 90) -> pd.DataFrame | None:
    """
    Return recent predictions from the database for all horizons.
    """
    query = """
        SELECT date, predicted_level, flood_probability, days_ahead, created_at
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

def get_prediction(date: str, days_ahead: int) -> Optional[dict]:
    """Retrieve cached prediction for a given date and days_ahead."""
    query = """
        SELECT predicted_level, flood_probability, days_ahead, created_at
        FROM predictions
        WHERE date = %s AND days_ahead = %s
        LIMIT 1
    """

    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=(date, days_ahead))
        conn.close()

        if df.empty:
            return None

        row = df.iloc[0]
        return {
            'predicted_level': float(row['predicted_level']) if row['predicted_level'] is not None else None,
            'flood_probability': float(row['flood_probability']) if row['flood_probability'] is not None else None,
            'days_ahead': int(row['days_ahead']) if row['days_ahead'] is not None else None,
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
        SELECT date, predicted_level, flood_probability, days_ahead, created_at
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
            'date': str(row['date']),
            'predicted_level': float(row['predicted_level']) if row['predicted_level'] is not None else None,
            'flood_probability': float(row['flood_probability']) if row['flood_probability'] is not None else None,
            'days_ahead': int(row['days_ahead']) if row['days_ahead'] is not None else None,
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
