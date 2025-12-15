"""
Test database setup utilities for pytest fixtures.
"""
import pytest
import psycopg2
from sqlalchemy import create_engine, text
import os

# Test database configuration
TEST_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5433)),
    'database': os.getenv('DB_NAME', 'test_flood_prediction'),
    'user': os.getenv('DB_USER', 'test_user'),
    'password': os.getenv('DB_PASSWORD', 'test_password'),
}


@pytest.fixture(scope='session')
def test_db_engine():
    """Create test database engine."""
    db_url = (
        f"postgresql://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}"
        f"@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}"
    )

    engine = create_engine(db_url)

    # Initialize test schema
    with engine.connect() as conn:
        # Create schema from the actual schema file
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'init', '01-schema.sql')
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
                conn.execute(text(schema_sql))

        # Insert test data
        _insert_test_data(conn)

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture
def test_db_connection(test_db_engine):
    """Create test database connection."""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    conn.autocommit = True
    yield conn
    conn.close()


def _insert_test_data(conn):
    """Insert test data for integration tests."""
    # Insert test zones
    zones_data = [
        ("ZONE_001", "Downtown St. Louis", 0.9, 0.3, 0.8, 0.7, 2, True),
        ("ZONE_002", "West End", 0.6, 0.5, 0.4, 0.3, 0, False),
        ("ZONE_003", "North County", 0.2, 0.8, 0.3, 0.2, 1, False),
    ]

    for zone_data in zones_data:
        conn.execute("""
            INSERT INTO zones (zone_id, name, river_proximity, elevation_risk, pop_density, crit_infra_score, hospital_count, critical_infra)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (zone_id) DO NOTHING
        """, zone_data)

    # Insert test resource types
    resource_data = [
        ("R1_UAV", "UAV Surveillance", "Unmanned aerial vehicles for reconnaissance", "drone", 1, 5),
        ("R2_ENGINEERING", "Engineering Teams", "Civil engineering response teams", "engineering", 2, 10),
        ("R3_PUMPS", "Water Pumps", "High-capacity water pumping equipment", "pump", 3, 15),
        ("R4_RESCUE", "Rescue Teams", "Search and rescue personnel", "rescue", 4, 8),
        ("R5_EVAC", "Evacuation Support", "Evacuation coordination and transport", "evac", 5, 12),
        ("R6_MEDICAL", "Medical Teams", "Emergency medical response teams", "medical", 6, 6),
        ("R7_CI", "Critical Infrastructure", "Infrastructure protection and repair", "infra", 7, 4),
    ]

    for resource in resource_data:
        conn.execute("""
            INSERT INTO resource_types (resource_id, name, description, icon, display_order, capacity)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (resource_id) DO NOTHING
        """, resource)

    # Insert test raw data
    from datetime import datetime, timedelta

    base_date = datetime.now() - timedelta(days=30)
    raw_data = []

    for i in range(30):
        date = base_date + timedelta(days=i)
        raw_data.append((
            date.date(),
            0.1 + i * 0.01,  # daily_precip
            20.0 + i * 0.1,  # daily_temp_avg
            0.0,  # daily_snowfall
            0.6 + i * 0.001,  # daily_humidity
            5.0 + i * 0.01,  # daily_wind
            0.3 + i * 0.001,  # soil_deep_30d
            10.0 + i * 0.1,  # target_level_max
            9.0 + i * 0.1,   # hermann_level
            8.0 + i * 0.1,   # grafton_level
        ))

    conn.executemany("""
        INSERT INTO raw_data (date, daily_precip, daily_temp_avg, daily_snowfall, daily_humidity, daily_wind, soil_deep_30d, target_level_max, hermann_level, grafton_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date) DO NOTHING
    """, raw_data)

    # Insert test predictions
    prediction_data = []
    for lead_time in [1, 2, 3]:
        for i in range(5):  # 5 predictions per lead time
            date = datetime.now() + timedelta(days=lead_time + i)
            prediction_data.append((
                date.date(),
                lead_time,
                f"v1.0.0-test",
                10.0 + lead_time + i * 0.5,  # predicted_level
                9.5 + lead_time + i * 0.5,   # lower_bound_80
                10.5 + lead_time + i * 0.5,  # upper_bound_80
                0.1 + i * 0.05,              # flood_probability
                "ensemble"  # model_type
            ))

    conn.executemany("""
        INSERT INTO predictions (date, days_ahead, model_version, predicted_level, lower_bound_80, upper_bound_80, flood_probability, model_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date, days_ahead) DO NOTHING
    """, prediction_data)