"""Tests for health check endpoint."""
import pytest
from httpx import AsyncClient


class TestHealth:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint returns OK status."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_response_format(self, client: AsyncClient):
        """Test health endpoint returns correct format."""
        response = await client.get("/health")
        data = response.json()
        
        assert isinstance(data["status"], str)
        assert isinstance(data["database"], str)
        assert isinstance(data["version"], str)
