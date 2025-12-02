"""Tests for zones endpoints."""
import pytest
from httpx import AsyncClient


class TestZones:
    """Test zone endpoints."""

    @pytest.mark.asyncio
    async def test_get_zones(self, client: AsyncClient):
        """Test getting all zones."""
        response = await client.get("/api/zones")
        assert response.status_code == 200
        
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert isinstance(data["features"], list)

    @pytest.mark.asyncio
    async def test_zones_geojson_format(self, client: AsyncClient):
        """Test zones are returned in valid GeoJSON format."""
        response = await client.get("/api/zones")
        data = response.json()
        
        if len(data["features"]) > 0:
            feature = data["features"][0]
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
            
            props = feature["properties"]
            assert "id" in props
            assert "name" in props

    @pytest.mark.asyncio
    async def test_zones_properties(self, client: AsyncClient):
        """Test zone properties contain expected fields."""
        response = await client.get("/api/zones")
        data = response.json()
        
        if len(data["features"]) > 0:
            props = data["features"][0]["properties"]
            expected_fields = ["id", "name", "description", "population", "critical_assets", "admin_level"]
            for field in expected_fields:
                assert field in props, f"Missing field: {field}"
