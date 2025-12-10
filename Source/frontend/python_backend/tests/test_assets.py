"""Tests for assets endpoints."""
import pytest
from httpx import AsyncClient


class TestAssets:
    """Test asset endpoints."""

    @pytest.mark.asyncio
    async def test_get_assets(self, client: AsyncClient):
        """Test getting all assets."""
        response = await client.get("/api/assets")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_assets_structure(self, client: AsyncClient):
        """Test asset response structure."""
        response = await client.get("/api/assets")
        data = response.json()
        
        if len(data) > 0:
            asset = data[0]
            expected_fields = ["id", "zoneId", "name", "type", "criticality"]
            for field in expected_fields:
                assert field in asset, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_assets_filter_by_zone(self, client: AsyncClient):
        """Test filtering assets by zone."""
        response = await client.get("/api/assets", params={"zoneId": "Z1N"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # All returned assets should be from the specified zone
        for asset in data:
            assert asset["zoneId"] == "Z1N"

    @pytest.mark.asyncio
    async def test_assets_location_format(self, client: AsyncClient):
        """Test asset location data format."""
        response = await client.get("/api/assets")
        data = response.json()
        
        if len(data) > 0:
            asset = data[0]
            # Location can be null or a GeoJSON point
            if asset.get("location"):
                assert asset["location"]["type"] == "Point"
                assert "coordinates" in asset["location"]
