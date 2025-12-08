"""Test fixtures and configuration."""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
import json

from app.main import app
from app.database import get_db, Base
from app.config import get_settings


# Test database URL - uses the same PostgreSQL database
settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine(event_loop):
    """Create test database engine."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=5,
        max_overflow=0,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    session = async_session()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_zone_geojson():
    """Sample GeoJSON for zone testing."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "properties": {
                    "id": "TEST-ZONE",
                    "name": "Test Zone",
                    "description": "A test zone",
                    "population": 1000,
                    "critical_assets": ["Hospital"],
                    "admin_level": 10
                }
            }
        ]
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for admin testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "role": "Planner",
        "department": "Operations",
        "status": "active",
        "zones": [],
        "permissions": []
    }


@pytest.fixture
def sample_risk_threshold():
    """Sample risk threshold data."""
    return {
        "name": "Test Threshold",
        "band": "High",
        "minRisk": 0.5,
        "maxRisk": 0.75,
        "color": "#ff0000",
        "description": "Test threshold",
        "autoAlert": True
    }


@pytest.fixture
def sample_gauge_threshold():
    """Sample gauge threshold data."""
    return {
        "gaugeCode": "TEST-GAUGE",
        "gaugeName": "Test Gauge",
        "alertThreshold": 2.5,
        "criticalThreshold": 3.5,
        "unit": "meters",
        "description": "Test gauge threshold"
    }


@pytest.fixture
def sample_alert_rule():
    """Sample alert rule data."""
    return {
        "name": "Test Rule",
        "triggerType": "risk_level",
        "triggerValue": "0.75",
        "severity": "high",
        "enabled": True,
        "channels": ["Dashboard", "Email"],
        "cooldownMinutes": 30,
        "description": "Test alert rule"
    }


@pytest.fixture
def sample_communication():
    """Sample communication data."""
    return {
        "channel": "Radio",
        "from": "Control Center",
        "to": "Field Team Alpha",
        "text": "Test message",
        "priority": "high"
    }


@pytest.fixture
def sample_plan_draft():
    """Sample draft plan data."""
    return {
        "name": "Test Plan",
        "assignments": [
            {
                "zoneId": "Z-ALFA",
                "priority": 1,
                "actions": [
                    {"action": "deploy", "resource": "CREW-01", "quantity": 1}
                ]
            }
        ],
        "coverage": {"total": 1},
        "notes": "Test plan notes"
    }
