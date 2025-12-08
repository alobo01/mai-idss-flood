"""Tests for resources endpoints."""
import pytest
from httpx import AsyncClient


class TestResources:
    """Test resource endpoints."""

    @pytest.mark.asyncio
    async def test_get_resources(self, client: AsyncClient):
        """Test getting all resources."""
        response = await client.get("/api/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "depots" in data
        assert "equipment" in data
        assert "crews" in data

    @pytest.mark.asyncio
    async def test_resources_depots_structure(self, client: AsyncClient):
        """Test depot resource structure."""
        response = await client.get("/api/resources")
        data = response.json()
        
        if len(data["depots"]) > 0:
            depot = data["depots"][0]
            assert "id" in depot
            assert "name" in depot
            assert "lat" in depot
            assert "lng" in depot

    @pytest.mark.asyncio
    async def test_resources_equipment_structure(self, client: AsyncClient):
        """Test equipment resource structure."""
        response = await client.get("/api/resources")
        data = response.json()
        
        if len(data["equipment"]) > 0:
            equip = data["equipment"][0]
            assert "id" in equip
            assert "type" in equip
            assert "status" in equip

    @pytest.mark.asyncio
    async def test_resources_crews_structure(self, client: AsyncClient):
        """Test crew resource structure."""
        response = await client.get("/api/resources")
        data = response.json()
        
        if len(data["crews"]) > 0:
            crew = data["crews"][0]
            assert "id" in crew
            assert "name" in crew
            assert "skills" in crew
            assert "status" in crew

    @pytest.mark.asyncio
    async def test_resources_filter_by_type(self, client: AsyncClient):
        """Test filtering resources by type."""
        response = await client.get("/api/resources", params={"type": "crew"})
        assert response.status_code == 200
        
        data = response.json()
        # When filtering by crew, only crews should have items
        assert len(data["depots"]) == 0
        assert len(data["equipment"]) == 0

    @pytest.mark.asyncio
    async def test_resources_filter_by_status(self, client: AsyncClient):
        """Test filtering resources by status."""
        response = await client.get("/api/resources", params={"status": "available"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
