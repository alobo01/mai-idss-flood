"""Tests for error handling and edge cases."""
import pytest
from httpx import AsyncClient


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_404_endpoint(self, client: AsyncClient):
        """Test 404 for non-existent endpoints."""
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_json_body(self, client: AsyncClient):
        """Test handling of invalid JSON body."""
        response = await client.post(
            "/api/comms",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test handling of missing required fields."""
        response = await client.post("/api/admin/users", json={})
        assert response.status_code == 422


class TestQueryParameters:
    """Test query parameter handling."""

    @pytest.mark.asyncio
    async def test_invalid_limit_value(self, client: AsyncClient):
        """Test handling of invalid limit value."""
        response = await client.get("/api/alerts", params={"limit": -1})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_exceeds_max(self, client: AsyncClient):
        """Test limit is capped at maximum."""
        response = await client.get("/api/alerts", params={"limit": 1000})
        assert response.status_code == 422  # Should fail validation


class TestContentTypes:
    """Test content type handling."""

    @pytest.mark.asyncio
    async def test_json_response_type(self, client: AsyncClient):
        """Test responses are JSON."""
        response = await client.get("/health")
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_geojson_response(self, client: AsyncClient):
        """Test GeoJSON responses."""
        response = await client.get("/api/zones")
        assert "application/json" in response.headers["content-type"]
        
        data = response.json()
        assert data["type"] == "FeatureCollection"
