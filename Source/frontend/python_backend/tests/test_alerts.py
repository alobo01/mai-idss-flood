"""Tests for alerts endpoints."""
import pytest
from httpx import AsyncClient


class TestAlerts:
    """Test alert endpoints."""

    @pytest.mark.asyncio
    async def test_get_alerts(self, client: AsyncClient):
        """Test getting all alerts."""
        response = await client.get("/api/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_alerts_structure(self, client: AsyncClient):
        """Test alert response structure."""
        response = await client.get("/api/alerts")
        data = response.json()
        
        if len(data) > 0:
            alert = data[0]
            expected_fields = ["id", "zoneId", "severity", "type", "title", "description", "status", "timestamp"]
            for field in expected_fields:
                assert field in alert, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_alerts_severity_filter(self, client: AsyncClient):
        """Test filtering alerts by severity."""
        response = await client.get("/api/alerts", params={"severity": "high"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_alerts_limit(self, client: AsyncClient):
        """Test alert limit parameter."""
        response = await client.get("/api/alerts", params={"limit": 5})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_alerts_severity_display(self, client: AsyncClient):
        """Test alert severity is properly displayed."""
        response = await client.get("/api/alerts")
        data = response.json()
        
        valid_severities = ["Low", "Moderate", "High", "Severe"]
        for alert in data:
            assert alert["severity"] in valid_severities, f"Invalid severity: {alert['severity']}"

    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self, client: AsyncClient):
        """Test acknowledging non-existent alert."""
        response = await client.post(
            "/api/alerts/non-existent-id/ack",
            json={"acknowledgedBy": "test_user"}
        )
        assert response.status_code == 404
