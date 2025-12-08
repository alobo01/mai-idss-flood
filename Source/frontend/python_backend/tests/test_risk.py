"""Tests for risk, damage index, and gauge endpoints."""
import pytest
from httpx import AsyncClient


class TestRisk:
    """Test risk endpoints."""

    @pytest.mark.asyncio
    async def test_get_risk(self, client: AsyncClient):
        """Test getting risk data."""
        response = await client.get("/api/risk")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_risk_structure(self, client: AsyncClient):
        """Test risk response structure."""
        response = await client.get("/api/risk")
        data = response.json()
        
        if len(data) > 0:
            risk = data[0]
            expected_fields = ["zoneId", "risk", "drivers", "thresholdBand", "etaHours"]
            for field in expected_fields:
                assert field in risk, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_risk_time_horizon(self, client: AsyncClient):
        """Test risk with time horizon parameter."""
        for horizon in ["6h", "12h", "24h", "48h"]:
            response = await client.get("/api/risk", params={"timeHorizon": horizon})
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_risk_threshold_bands(self, client: AsyncClient):
        """Test risk threshold bands are valid."""
        response = await client.get("/api/risk")
        data = response.json()
        
        valid_bands = ["Low", "Moderate", "High", "Severe"]
        for item in data:
            assert item["thresholdBand"] in valid_bands

    @pytest.mark.asyncio
    async def test_risk_values_range(self, client: AsyncClient):
        """Test risk values are in valid range 0-1."""
        response = await client.get("/api/risk")
        data = response.json()
        
        for item in data:
            assert 0 <= item["risk"] <= 1


class TestDamageIndex:
    """Test damage index endpoints."""

    @pytest.mark.asyncio
    async def test_get_damage_index(self, client: AsyncClient):
        """Test getting damage index data."""
        response = await client.get("/api/damage-index")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_damage_index_structure(self, client: AsyncClient):
        """Test damage index response structure."""
        response = await client.get("/api/damage-index")
        data = response.json()
        
        if len(data) > 0:
            item = data[0]
            expected_fields = ["zoneId", "infra_index", "human_index", "notes"]
            for field in expected_fields:
                assert field in item, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_damage_index_values_range(self, client: AsyncClient):
        """Test damage index values are in valid range."""
        response = await client.get("/api/damage-index")
        data = response.json()
        
        for item in data:
            assert 0 <= item["infra_index"] <= 1
            assert 0 <= item["human_index"] <= 1


class TestGauges:
    """Test gauge endpoints."""

    @pytest.mark.asyncio
    async def test_get_gauges(self, client: AsyncClient):
        """Test getting gauge data."""
        response = await client.get("/api/gauges")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_gauges_structure(self, client: AsyncClient):
        """Test gauge response structure."""
        response = await client.get("/api/gauges")
        data = response.json()
        
        if len(data) > 0:
            gauge = data[0]
            expected_fields = ["id", "name", "lat", "lng", "level_m", "trend", "alert_threshold", "critical_threshold"]
            for field in expected_fields:
                assert field in gauge, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_gauges_trend_values(self, client: AsyncClient):
        """Test gauge trend values are valid."""
        response = await client.get("/api/gauges")
        data = response.json()
        
        valid_trends = ["rising", "falling", "steady"]
        for gauge in data:
            assert gauge["trend"] in valid_trends
