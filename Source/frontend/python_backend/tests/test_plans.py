"""Tests for response plan endpoints."""
import pytest
from httpx import AsyncClient


class TestPlans:
    """Test response plan endpoints."""

    @pytest.mark.asyncio
    async def test_get_plan(self, client: AsyncClient):
        """Test getting response plan."""
        response = await client.get("/api/plan")
        # May return 404 if no plan exists
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert "assignments" in data

    @pytest.mark.asyncio
    async def test_get_plan_with_status_filter(self, client: AsyncClient):
        """Test getting plan with status filter."""
        response = await client.get("/api/plan", params={"status": "draft"})
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_plan_with_type_filter(self, client: AsyncClient):
        """Test getting plan with type filter."""
        response = await client.get("/api/plan", params={"type": "resource_deployment"})
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_create_draft_plan(self, client: AsyncClient, sample_plan_draft):
        """Test creating a draft plan."""
        response = await client.post("/api/plan/draft", json=sample_plan_draft)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["status"] == "draft"
        assert data["name"] == sample_plan_draft["name"]
        assert len(data["assignments"]) == len(sample_plan_draft["assignments"])

    @pytest.mark.asyncio
    async def test_create_draft_plan_empty_assignments(self, client: AsyncClient):
        """Test creating draft plan with empty assignments fails."""
        response = await client.post("/api/plan/draft", json={"assignments": []})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_draft_plan_invalid_assignment(self, client: AsyncClient):
        """Test creating draft plan with invalid assignment."""
        invalid_plan = {
            "assignments": [
                {"zoneId": "", "actions": []}  # Empty zoneId and actions
            ]
        }
        response = await client.post("/api/plan/draft", json=invalid_plan)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_draft_plan_structure(self, client: AsyncClient, sample_plan_draft):
        """Test draft plan response structure."""
        response = await client.post("/api/plan/draft", json=sample_plan_draft)
        data = response.json()
        
        expected_fields = [
            "id", "name", "planType", "status", "version", 
            "assignments", "coverage", "notes", "createdAt", "updatedAt"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_create_draft_plan_default_values(self, client: AsyncClient):
        """Test draft plan with minimal data gets default values."""
        minimal_plan = {
            "assignments": [
                {
                    "zoneId": "Z2",
                    "actions": [{"action": "deploy"}]
                }
            ]
        }
        response = await client.post("/api/plan/draft", json=minimal_plan)
        assert response.status_code == 201
        
        data = response.json()
        assert data["planType"] == "resource_deployment"
        assert data["priority"] == "medium"
