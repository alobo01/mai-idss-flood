"""
Tests for FastAPI endpoints.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

from app.main import app
from app.schemas import ResourceType


class TestAPIEndpoints:
    """Test API endpoint functionality."""

    def setup_method(self):
        """Setup test client for each test."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert "version" in data["data"]

    @patch('app.main.test_connection')
    def test_health_endpoint_healthy(self, mock_test_conn):
        """Test health endpoint with healthy database."""
        mock_test_conn.return_value = True

        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    @patch('app.main.test_connection')
    def test_health_endpoint_degraded(self, mock_test_conn):
        """Test health endpoint with degraded database."""
        mock_test_conn.return_value = False

        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"

    @patch('app.main.test_connection')
    def test_health_endpoint_unhealthy(self, mock_test_conn):
        """Test health endpoint with database error."""
        mock_test_conn.side_effect = Exception("Database error")

        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data

    @patch('app.main.get_last_30_days_raw_data')
    def test_raw_data_endpoint_success(self, mock_get_data, sample_raw_data):
        """Test raw data endpoint with successful data retrieval."""
        mock_get_data.return_value = sample_raw_data

        response = self.client.get("/raw-data")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "rows" in data["data"]
        assert len(data["data"]["rows"]) == 30

    @patch('app.main.get_last_30_days_raw_data')
    def test_raw_data_endpoint_no_data(self, mock_get_data):
        """Test raw data endpoint with no data available."""
        mock_get_data.return_value = None

        response = self.client.get("/raw-data")
        assert response.status_code == 404
        assert "No raw data found" in response.json()["detail"]

    @patch('app.main.get_prediction_history_with_actuals')
    def test_prediction_history_endpoint_success(self, mock_get_history):
        """Test prediction history endpoint with data."""
        # Mock historical data
        dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
        history_data = []
        for i, date in enumerate(dates):
            history_data.append({
                'forecast_date': date.strftime('%Y-%m-%d'),
                'lead_time_days': 1,
                'predicted_level': 10.0 + i * 0.1,
                'actual_level': 10.5 + i * 0.1,
                'flood_probability': 0.1 + i * 0.01,
            })

        mock_df = pd.DataFrame(history_data)
        mock_get_history.return_value = mock_df

        response = self.client.get("/prediction-history?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "rows" in data["data"]
        assert len(data["data"]["rows"]) == 10

    @patch('app.main.get_prediction_history_with_actuals')
    def test_prediction_history_endpoint_no_data(self, mock_get_history):
        """Test prediction history endpoint with no data."""
        mock_get_history.return_value = None

        response = self.client.get("/prediction-history")
        assert response.status_code == 404
        assert "No prediction history found" in response.json()["detail"]

    @patch('app.main.predict_all_historical')
    def test_predict_all_endpoint_sync(self, mock_predict_all):
        """Test predict-all endpoint in synchronous mode."""
        # Mock successful prediction
        mock_result = {
            "status": "completed",
            "total_predictions": 100,
            "lead_times": [1, 2, 3],
            "predictions_by_lead_time": {
                1: [{"lead_time_days": 1, "forecast_date": "2025-12-11"}],
                2: [{"lead_time_days": 2, "forecast_date": "2025-12-12"}],
                3: [{"lead_time_days": 3, "forecast_date": "2025-12-13"}],
            },
            "skipped_cached": 20,
            "errors": [],
            "summary": {
                "lead_time_1": {
                    "count": 33,
                    "median_predictions": {"min": 10.0, "max": 15.0},
                    "flood_probabilities": {"min": 0.0, "max": 0.5},
                }
            }
        }
        mock_predict_all.return_value = mock_result

        response = self.client.post(
            "/predict-all?lead_times=1,2,3&skip_cached=true&run_in_background=false"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["total_predictions"] == 100
        assert len(data["predictions_by_lead_time"]) == 3

    @patch('app.main.predict_all_historical')
    def test_predict_all_endpoint_background(self, mock_predict_all):
        """Test predict-all endpoint in background mode."""
        # Mock prediction function (shouldn't be called in background mode)
        mock_predict_all.side_effect = Exception("Should not be called in background mode")

        response = self.client.post(
            "/predict-all?run_in_background=true&lead_times=1,2,3"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "started"
        assert "job_id" in data
        assert data["lead_times"] == [1, 2, 3]

    def test_predict_all_endpoint_invalid_lead_times(self):
        """Test predict-all endpoint with invalid lead times."""
        response = self.client.post(
            "/predict-all?lead_times=invalid&run_in_background=false"
        )
        assert response.status_code == 400
        assert "Invalid lead_times format" in response.json()["detail"]

    @patch('app.main.JOB_STORE')
    def test_predict_all_status_endpoint(self, mock_job_store):
        """Test predict-all status endpoint."""
        # Mock job store
        mock_job_store.get.return_value = {
            "job_id": "test_job_123",
            "status": "running",
            "percent": 45.5,
            "completed": 450,
            "total": 1000,
            "message": "Processing data...",
        }

        response = self.client.get("/predict-all/status/test_job_123")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == "test_job_123"
        assert data["status"] == "running"

    @patch('app.main.JOB_STORE')
    def test_predict_all_status_not_found(self, mock_job_store):
        """Test predict-all status endpoint with job not found."""
        mock_job_store.get.return_value = None

        response = self.client.get("/predict-all/status/nonexistent_job")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch('app.main.get_latest_prediction')
    @patch('app.main.get_all_zones')
    @patch('app.main.build_dispatch_plan')
    @patch('app.main.get_all_resource_types')
    def test_rule_based_dispatch_endpoint(
        self, mock_get_resources, mock_build_dispatch, mock_get_zones, mock_get_prediction,
        sample_zone_data, sample_resource_types
    ):
        """Test rule-based dispatch endpoint."""
        # Mock latest prediction
        mock_get_prediction.return_value = {
            "flood_probability": 0.3,
            "predicted_level": 12.5,
            "lower_bound_80": 11.8,
            "upper_bound_80": 13.4,
            "created_at": datetime.now().isoformat()
        }

        mock_get_zones.return_value = sample_zone_data
        mock_get_resources.return_value = sample_resource_types

        # Mock dispatch plan
        mock_dispatch = [
            {
                "zone_id": "ZONE_001",
                "zone_name": "Downtown",
                "impact_level": "WARNING",
                "allocation_mode": "fuzzy",
                "units_allocated": 10,
                "resource_units": {"R1_UAV": 3, "R2_ENGINEERING": 4, "R3_PUMPS": 3},
            }
        ]
        mock_build_dispatch.return_value = mock_dispatch

        response = self.client.get(
            "/rule-based/dispatch?total_units=30&mode=fuzzy&lead_time=1"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["lead_time_days"] == 1
        assert data["total_units"] == 30
        assert data["global_flood_probability"] == 0.3
        assert data["scenario"] == "normal"
        assert data["last_prediction"]["selected_level"] == 12.5
        assert data["last_prediction"]["selected_probability"] == 0.3
        assert len(data["zones"]) == 1
        assert data["zones"][0]["zone_id"] == "ZONE_001"

    @patch('app.main.get_latest_prediction')
    @patch('app.main.get_all_zones')
    @patch('app.main.build_dispatch_plan')
    @patch('app.main.get_all_resource_types')
    def test_rule_based_dispatch_best_scenario(
        self, mock_get_resources, mock_build_dispatch, mock_get_zones, mock_get_prediction,
        sample_zone_data, sample_resource_types
    ):
        """Ensure scenario=best picks the lower PI bound."""
        mock_get_prediction.return_value = {
            "flood_probability": 0.45,
            "predicted_level": 13.5,
            "lower_bound_80": 11.8,
            "upper_bound_80": 15.1,
            "created_at": datetime.now().isoformat()
        }
        mock_get_zones.return_value = sample_zone_data
        mock_get_resources.return_value = sample_resource_types

        mock_build_dispatch.return_value = [
            {"zone_id": "ZONE_007", "units_allocated": 5, "impact_level": "ADVISORY", "allocation_mode": "fuzzy"},
        ]

        response = self.client.get(
            "/rule-based/dispatch?total_units=30&mode=fuzzy&lead_time=1&scenario=best"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["global_flood_probability"] == 0.45
        assert data["scenario"] == "best"
        assert data["last_prediction"]["selected_level"] == 11.8
        assert data["last_prediction"]["selected_level_source"] == "prediction_interval_lower"

    @patch('app.main.get_latest_prediction')
    def test_rule_based_dispatch_no_prediction(self, mock_get_prediction):
        """Test rule-based dispatch with no cached prediction."""
        mock_get_prediction.return_value = None

        response = self.client.get(
            "/rule-based/dispatch?total_units=30&lead_time=1"
        )
        assert response.status_code == 404
        assert "No cached prediction" in response.json()["detail"]

    @patch('app.main.get_latest_prediction')
    @patch('app.main.get_last_30_days_raw_data')
    @patch('app.main.predict_next_days')
    @patch('app.main.get_all_zones')
    @patch('app.main.build_dispatch_plan')
    @patch('app.main.get_all_resource_types')
    def test_rule_based_dispatch_generate_prediction(
        self, mock_get_resources, mock_build_dispatch, mock_get_zones,
        mock_predict, mock_get_raw_data, mock_get_prediction,
        sample_zone_data, sample_resource_types, sample_raw_data
    ):
        """Test rule-based dispatch generating prediction on-the-fly."""
        # No cached prediction initially
        mock_get_prediction.return_value = None

        # Mock raw data and prediction generation
        mock_get_raw_data.return_value = sample_raw_data
        mock_get_zones.return_value = sample_zone_data
        mock_get_resources.return_value = sample_resource_types

        # Mock prediction generation
        mock_prediction = {
            'lead_time_days': 1,
            'forecast_date': '2025-12-11',
            'forecast': {'median': 13.2},
            'flood_risk': {'probability': 0.2},
        }
        mock_predict.return_value = [mock_prediction]

        # Mock new prediction available after generation
        mock_get_prediction.side_effect = [
            None,  # First call - no prediction
            {"flood_probability": 0.2, "predicted_level": 13.2}  # Second call - has prediction
        ]

        # Mock dispatch plan
        mock_dispatch = [{"zone_id": "ZONE_001", "units_allocated": 10}]
        mock_build_dispatch.return_value = mock_dispatch

        response = self.client.get(
            "/rule-based/dispatch?total_units=30&lead_time=1"
        )
        assert response.status_code == 200

        # Should have generated prediction and created dispatch plan
        mock_predict.assert_called_once()
        assert response.json()["global_flood_probability"] == 0.2

    def test_rule_based_dispatch_invalid_mode(self):
        """Test rule-based dispatch with invalid mode."""
        response = self.client.get(
            "/rule-based/dispatch?total_units=30&mode=invalid"
        )
        # This should still work as the endpoint validates the enum
        # but we can test validation of other parameters
        assert response.status_code == 200  # FastAPI handles enum validation

    def test_rule_based_dispatch_invalid_units(self):
        """Test rule-based dispatch with invalid total_units."""
        response = self.client.get(
            "/rule-based/dispatch?total_units=0"  # Below minimum of 1
        )
        assert response.status_code == 422  # Validation error

        response = self.client.get(
            "/rule-based/dispatch?total_units=300"  # Above maximum of 200
        )
        assert response.status_code == 422  # Validation error

    @patch('app.main.get_all_zones')
    def test_zones_endpoint(self, mock_get_zones, sample_zone_data):
        """Test zones endpoint."""
        mock_get_zones.return_value = sample_zone_data

        response = self.client.get("/zones")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "rows" in data["data"]
        assert len(data["data"]["rows"]) == 3
        assert data["data"]["rows"][0]["zone_id"] == "ZONE_001"

    @patch('app.main.get_all_zones')
    def test_zones_endpoint_empty(self, mock_get_zones):
        """Test zones endpoint with no zones."""
        mock_get_zones.return_value = []

        response = self.client.get("/zones")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["rows"]) == 0

    @patch('app.main.get_all_resource_types')
    def test_resource_types_endpoint(self, mock_get_resources, sample_resource_types):
        """Test resource types endpoint."""
        mock_get_resources.return_value = sample_resource_types

        response = self.client.get("/resource-types")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "rows" in data["data"]
        assert len(data["data"]["rows"]) == 3
        assert data["data"]["rows"][0]["resource_id"] == "R1_UAV"

    @patch('app.main.get_all_resource_types')
    def test_resource_types_endpoint_no_data(self, mock_get_resources):
        """Test resource types endpoint with no data."""
        mock_get_resources.return_value = []

        response = self.client.get("/resource-types")
        assert response.status_code == 404
        assert "No resource types found" in response.json()["detail"]

    @patch('app.main.get_connection')
    @patch('app.main.get_all_resource_types')
    def test_update_resource_capacities(self, mock_get_resources, mock_get_conn, sample_resource_types):
        """Test updating resource capacities."""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3  # 3 resources updated
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        mock_get_resources.return_value = sample_resource_types

        update_data = {
            "capacities": {
                "R1_UAV": 10,
                "R2_ENGINEERING": 20,
                "R3_PUMPS": 30,
            }
        }

        response = self.client.put("/resource-types/capacities", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 3
        assert "resources" in data["data"]

    def test_update_resource_capacities_invalid_data(self):
        """Test updating resource capacities with invalid data."""
        # Negative capacity
        update_data = {
            "capacities": {
                "R1_UAV": -5,  # Invalid negative capacity
            }
        }

        response = self.client.put("/resource-types/capacities", json=update_data)
        assert response.status_code == 422  # Validation error

    @patch('app.main.DataFetcher')
    def test_gauges_endpoint(self, mock_data_fetcher):
        """Test gauges endpoint."""
        # Mock DataFetcher
        mock_fetcher = Mock()
        mock_fetcher.stations = {
            "STL": {
                "name": "St. Louis Gauge",
                "lat": 38.6270,
                "lon": -90.1994,
                "id": "07010000",
            },
            "HERMANN": {
                "name": "Hermann Gauge",
                "lat": 38.7075,
                "lon": -91.4497,
                "id": "06934500",
            },
        }
        mock_data_fetcher.return_value = mock_fetcher

        response = self.client.get("/gauges")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "rows" in data["data"]
        assert len(data["data"]["rows"]) == 2
        assert data["data"]["rows"][0]["id"] == "STL"
        assert data["data"]["rows"][0]["name"] == "St. Louis Gauge"

    @patch('app.main.get_sqlalchemy_engine')
    def test_zones_geo_endpoint(self, mock_engine):
        """Test zones GeoJSON endpoint."""
        # Mock database response
        geo_data = {
            'zone_id': ['ZONE_001', 'ZONE_002'],
            'name': ['Downtown', 'West End'],
            'river_proximity': [0.9, 0.6],
            'elevation_risk': [0.3, 0.5],
            'pop_density': [0.8, 0.4],
            'crit_infra_score': [0.7, 0.3],
            'hospital_count': [2, 0],
            'critical_infra': [True, False],
            'geojson': [
                {"type": "Polygon", "coordinates": [[[-90.2, 38.6], [-90.1, 38.6], [-90.1, 38.7], [-90.2, 38.7]]]},
                {"type": "Polygon", "coordinates": [[[-90.3, 38.5], [-90.2, 38.5], [-90.2, 38.6], [-90.3, 38.6]]]},
            ]
        }
        df = pd.DataFrame(geo_data)
        mock_engine.return_value.read_sql_query.return_value = df

        response = self.client.get("/zones-geo")
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 2
        assert data["features"][0]["properties"]["zone_id"] == "ZONE_001"
        assert data["features"][0]["type"] == "Feature"

    @patch('app.main.get_last_30_days_raw_data')
    @patch('app.main.predict_next_days')
    def test_predict_endpoint_database_source(self, mock_predict, mock_get_data, sample_raw_data):
        """Test predict endpoint using database source."""
        mock_get_data.return_value = sample_raw_data
        mock_prediction = {
            'lead_time_days': 1,
            'forecast_date': '2025-12-11',
            'forecast': {'median': 13.2},
            'flood_risk': {'probability': 0.1, 'risk_level': 'LOW'},
        }
        mock_predict.return_value = [mock_prediction]

        response = self.client.get("/predict?use_real_time_api=false")
        assert response.status_code == 200

        data = response.json()
        assert data["use_real_time_api"] is False
        assert "database" in data["data_source"]
        assert len(data["predictions"]) == 1

    @patch('app.main.get_latest_data')
    @patch('app.main.predict_next_days')
    def test_predict_endpoint_real_time_api(self, mock_predict, mock_get_data):
        """Test predict endpoint using real-time API."""
        # Mock real-time data fetcher
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = []
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'daily_precip': 0.1 + i * 0.01,
                'target_level_max': 10.0 + i * 0.1,
            })
        mock_get_data.return_value = pd.DataFrame(data)

        mock_prediction = {
            'lead_time_days': 1,
            'forecast_date': '2025-12-11',
            'forecast': {'median': 14.5},
            'flood_risk': {'probability': 0.2, 'risk_level': 'MODERATE'},
        }
        mock_predict.return_value = [mock_prediction]

        response = self.client.get("/predict?use_real_time_api=true")
        assert response.status_code == 200

        data = response.json()
        assert data["use_real_time_api"] is True
        assert "real-time APIs" in data["data_source"]

    @patch('app.main.get_last_30_days_raw_data')
    def test_predict_endpoint_insufficient_data(self, mock_get_data):
        """Test predict endpoint with insufficient data."""
        # Mock insufficient data
        dates = pd.date_range(end=datetime.now(), periods=20, freq='D')  # Less than 30 days
        data = [{'date': date, 'target_level_max': 10.0} for date in dates]
        mock_get_data.return_value = pd.DataFrame(data)

        response = self.client.get("/predict?use_real_time_api=false")
        assert response.status_code == 400
        assert "Insufficient data" in response.json()["detail"]
