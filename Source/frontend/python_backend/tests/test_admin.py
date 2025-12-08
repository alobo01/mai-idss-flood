"""Tests for admin endpoints."""
import pytest
from httpx import AsyncClient
import uuid


class TestAdminResources:
    """Test admin resource endpoints."""

    @pytest.mark.asyncio
    async def test_get_admin_depots(self, client: AsyncClient):
        """Test getting admin depots."""
        response = await client.get("/api/admin/resources/depots")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_admin_depot_structure(self, client: AsyncClient):
        """Test admin depot response structure."""
        response = await client.get("/api/admin/resources/depots")
        data = response.json()
        
        if len(data) > 0:
            depot = data[0]
            expected_fields = ["id", "name", "status", "lat", "lng"]
            for field in expected_fields:
                assert field in depot, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_get_admin_equipment(self, client: AsyncClient):
        """Test getting admin equipment."""
        response = await client.get("/api/admin/resources/equipment")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_admin_crews(self, client: AsyncClient):
        """Test getting admin crews."""
        response = await client.get("/api/admin/resources/crews")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestAdminUsers:
    """Test admin user management endpoints."""

    @pytest.mark.asyncio
    async def test_get_users(self, client: AsyncClient):
        """Test getting all users."""
        response = await client.get("/api/admin/users")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, sample_user_data):
        """Test creating a new user."""
        # Make username unique
        sample_user_data["username"] = f"testuser_{uuid.uuid4().hex[:8]}"
        sample_user_data["email"] = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        response = await client.post("/api/admin/users", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert data["role"] == sample_user_data["role"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, client: AsyncClient, sample_user_data):
        """Test creating duplicate user fails."""
        sample_user_data["username"] = f"dupuser_{uuid.uuid4().hex[:8]}"
        sample_user_data["email"] = f"dup_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create first user
        response1 = await client.post("/api/admin/users", json=sample_user_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = await client.post("/api/admin/users", json=sample_user_data)
        assert response2.status_code == 409

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, sample_user_data):
        """Test updating a user."""
        sample_user_data["username"] = f"updateuser_{uuid.uuid4().hex[:8]}"
        sample_user_data["email"] = f"update_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create user
        create_response = await client.post("/api/admin/users", json=sample_user_data)
        user_id = create_response.json()["id"]
        
        # Update user
        update_data = {"firstName": "Updated", "lastName": "Name"}
        response = await client.put(f"/api/admin/users/{user_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["firstName"] == "Updated"
        assert data["lastName"] == "Name"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client: AsyncClient):
        """Test updating non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/api/admin/users/{fake_id}", json={"firstName": "Test"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, sample_user_data):
        """Test deleting a user."""
        sample_user_data["username"] = f"deluser_{uuid.uuid4().hex[:8]}"
        sample_user_data["email"] = f"del_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create user
        create_response = await client.post("/api/admin/users", json=sample_user_data)
        user_id = create_response.json()["id"]
        
        # Delete user
        response = await client.delete(f"/api/admin/users/{user_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client: AsyncClient):
        """Test deleting non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/admin/users/{fake_id}")
        assert response.status_code == 404


class TestAdminRiskThresholds:
    """Test admin risk threshold endpoints."""

    @pytest.mark.asyncio
    async def test_get_risk_thresholds(self, client: AsyncClient):
        """Test getting risk thresholds."""
        response = await client.get("/api/admin/thresholds/risk")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_risk_threshold(self, client: AsyncClient, sample_risk_threshold):
        """Test creating a risk threshold."""
        response = await client.post("/api/admin/thresholds/risk", json=sample_risk_threshold)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_risk_threshold["name"]
        assert data["minRisk"] == sample_risk_threshold["minRisk"]
        assert data["maxRisk"] == sample_risk_threshold["maxRisk"]

    @pytest.mark.asyncio
    async def test_create_risk_threshold_invalid_values(self, client: AsyncClient):
        """Test creating risk threshold with invalid values."""
        invalid_threshold = {
            "name": "Invalid",
            "band": "Test",
            "minRisk": 0.8,
            "maxRisk": 0.5,  # max < min
        }
        response = await client.post("/api/admin/thresholds/risk", json=invalid_threshold)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_risk_threshold(self, client: AsyncClient, sample_risk_threshold):
        """Test updating a risk threshold."""
        # Create
        create_response = await client.post("/api/admin/thresholds/risk", json=sample_risk_threshold)
        threshold_id = create_response.json()["id"]
        
        # Update
        update_data = {"name": "Updated Threshold"}
        response = await client.put(f"/api/admin/thresholds/risk/{threshold_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Threshold"

    @pytest.mark.asyncio
    async def test_delete_risk_threshold(self, client: AsyncClient, sample_risk_threshold):
        """Test deleting a risk threshold."""
        # Create
        create_response = await client.post("/api/admin/thresholds/risk", json=sample_risk_threshold)
        threshold_id = create_response.json()["id"]
        
        # Delete
        response = await client.delete(f"/api/admin/thresholds/risk/{threshold_id}")
        assert response.status_code == 204


class TestAdminGaugeThresholds:
    """Test admin gauge threshold endpoints."""

    @pytest.mark.asyncio
    async def test_get_gauge_thresholds(self, client: AsyncClient):
        """Test getting gauge thresholds."""
        response = await client.get("/api/admin/thresholds/gauges")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_gauge_threshold(self, client: AsyncClient, sample_gauge_threshold):
        """Test creating a gauge threshold."""
        response = await client.post("/api/admin/thresholds/gauges", json=sample_gauge_threshold)
        assert response.status_code == 201
        
        data = response.json()
        assert data["gaugeCode"] == sample_gauge_threshold["gaugeCode"]
        assert data["gaugeName"] == sample_gauge_threshold["gaugeName"]

    @pytest.mark.asyncio
    async def test_update_gauge_threshold(self, client: AsyncClient, sample_gauge_threshold):
        """Test updating a gauge threshold."""
        # Create
        create_response = await client.post("/api/admin/thresholds/gauges", json=sample_gauge_threshold)
        threshold_id = create_response.json()["id"]
        
        # Update
        update_data = {"alertThreshold": 3.0}
        response = await client.put(f"/api/admin/thresholds/gauges/{threshold_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["alertThreshold"] == 3.0

    @pytest.mark.asyncio
    async def test_delete_gauge_threshold(self, client: AsyncClient, sample_gauge_threshold):
        """Test deleting a gauge threshold."""
        # Create
        create_response = await client.post("/api/admin/thresholds/gauges", json=sample_gauge_threshold)
        threshold_id = create_response.json()["id"]
        
        # Delete
        response = await client.delete(f"/api/admin/thresholds/gauges/{threshold_id}")
        assert response.status_code == 204


class TestAdminAlertRules:
    """Test admin alert rule endpoints."""

    @pytest.mark.asyncio
    async def test_get_alert_rules(self, client: AsyncClient):
        """Test getting alert rules."""
        response = await client.get("/api/admin/alerts/rules")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_alert_rule(self, client: AsyncClient, sample_alert_rule):
        """Test creating an alert rule."""
        response = await client.post("/api/admin/alerts/rules", json=sample_alert_rule)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_alert_rule["name"]
        assert data["triggerType"] == sample_alert_rule["triggerType"]

    @pytest.mark.asyncio
    async def test_update_alert_rule(self, client: AsyncClient, sample_alert_rule):
        """Test updating an alert rule."""
        # Create
        create_response = await client.post("/api/admin/alerts/rules", json=sample_alert_rule)
        rule_id = create_response.json()["id"]
        
        # Update
        update_data = {"enabled": False}
        response = await client.put(f"/api/admin/alerts/rules/{rule_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["enabled"] == False

    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, client: AsyncClient, sample_alert_rule):
        """Test deleting an alert rule."""
        # Create
        create_response = await client.post("/api/admin/alerts/rules", json=sample_alert_rule)
        rule_id = create_response.json()["id"]
        
        # Delete
        response = await client.delete(f"/api/admin/alerts/rules/{rule_id}")
        assert response.status_code == 204


class TestAdminExport:
    """Test admin export endpoints."""

    @pytest.mark.asyncio
    async def test_export_users(self, client: AsyncClient):
        """Test exporting users."""
        response = await client.get("/api/admin/export/users")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_export_thresholds(self, client: AsyncClient):
        """Test exporting thresholds."""
        response = await client.get("/api/admin/export/thresholds")
        assert response.status_code == 200
        
        data = response.json()
        assert "risk" in data
        assert "gauges" in data
        assert "alerts" in data

    @pytest.mark.asyncio
    async def test_export_resources(self, client: AsyncClient):
        """Test exporting resources."""
        response = await client.get("/api/admin/export/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "depots" in data
        assert "equipment" in data
        assert "crews" in data

    @pytest.mark.asyncio
    async def test_export_zones(self, client: AsyncClient):
        """Test exporting zones."""
        response = await client.get("/api/admin/export/zones")
        assert response.status_code == 200
        
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data

    @pytest.mark.asyncio
    async def test_export_invalid_type(self, client: AsyncClient):
        """Test exporting with invalid type."""
        response = await client.get("/api/admin/export/invalid")
        assert response.status_code == 400
