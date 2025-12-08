"""Tests for communications endpoints."""
import pytest
from httpx import AsyncClient


class TestCommunications:
    """Test communication endpoints."""

    @pytest.mark.asyncio
    async def test_get_communications(self, client: AsyncClient):
        """Test getting communications."""
        response = await client.get("/api/comms")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_communications_structure(self, client: AsyncClient):
        """Test communication response structure."""
        response = await client.get("/api/comms")
        data = response.json()
        
        if len(data) > 0:
            comm = data[0]
            expected_fields = ["id", "channel", "from", "to", "priority", "text", "timestamp"]
            for field in expected_fields:
                assert field in comm, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_communications_filter_channel(self, client: AsyncClient):
        """Test filtering communications by channel."""
        response = await client.get("/api/comms", params={"channel": "Radio"})
        assert response.status_code == 200
        
        data = response.json()
        for comm in data:
            assert comm["channel"] == "Radio"

    @pytest.mark.asyncio
    async def test_communications_filter_priority(self, client: AsyncClient):
        """Test filtering communications by priority."""
        response = await client.get("/api/comms", params={"priority": "high"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_communications_limit(self, client: AsyncClient):
        """Test communication limit parameter."""
        response = await client.get("/api/comms", params={"limit": 10})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_create_communication(self, client: AsyncClient, sample_communication):
        """Test creating a new communication."""
        response = await client.post("/api/comms", json=sample_communication)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["channel"] == sample_communication["channel"]
        assert data["from"] == sample_communication["from"]
        assert data["text"] == sample_communication["text"]

    @pytest.mark.asyncio
    async def test_create_communication_missing_fields(self, client: AsyncClient):
        """Test creating communication with missing required fields."""
        response = await client.post("/api/comms", json={"channel": "Radio"})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_communication_priority_validation(self, client: AsyncClient, sample_communication):
        """Test communication priority normalization."""
        sample_communication["priority"] = "invalid_priority"
        response = await client.post("/api/comms", json=sample_communication)
        assert response.status_code == 201
        
        data = response.json()
        # Invalid priority should default to 'normal'
        assert data["priority"] == "normal"
