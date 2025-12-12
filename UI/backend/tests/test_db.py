"""
Tests for database operations and models.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.db import (
    get_connection,
    test_connection,
    get_last_30_days_raw_data,
    get_all_raw_data,
    insert_prediction,
    get_prediction,
    get_all_zones,
    get_all_resource_types,
    insert_zone,
    insert_resource_type,
    insert_raw_data_batch,
    get_all_resource_types_typed,
)
from app.db_models import (
    PredictionInsert,
    ZoneInsert,
    ResourceTypeInsert,
    RawDataInsert,
    PredictionDAO,
    ZoneDAO,
    ResourceTypeDAO,
)
from app.schemas import Zone, ResourceType


class TestDatabaseConnection:
    """Test database connection functions."""

    @patch('app.db.psycopg2.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        conn = get_connection()
        assert conn == mock_conn
        mock_connect.assert_called_once()

    @patch('app.db.psycopg2.connect')
    def test_get_connection_failure(self, mock_connect):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            get_connection()

    @patch('app.db.get_connection')
    def test_test_connection_success(self, mock_get_conn):
        """Test successful connection test."""
        mock_conn = Mock()
        mock_get_conn.return_value = mock_conn

        result = test_connection()
        assert result is True
        mock_conn.close.assert_called_once()

    @patch('app.db.get_connection')
    def test_test_connection_failure(self, mock_get_conn):
        """Test connection test failure."""
        mock_get_conn.side_effect = Exception("Connection failed")

        result = test_connection()
        assert result is False


class TestPredictionOperations:
    """Test prediction-related database operations."""

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_last_30_days_raw_data_success(self, mock_engine):
        """Test successful retrieval of last 30 days raw data."""
        # Setup mock data
        dates = pd.date_range(end='2025-12-10', periods=30, freq='D')
        data = {
            'date': dates,
            'daily_precip': [0.1] * 30,
            'target_level_max': [10.0 + i * 0.1 for i in range(30)],
        }
        df = pd.DataFrame(data)

        # Setup mock
        mock_read_sql = Mock(return_value=df)
        mock_engine.return_value.read_sql_query = mock_read_sql

        result = get_last_30_days_raw_data()

        assert result is not None
        assert len(result) == 30
        assert 'date' in result.columns
        mock_read_sql.assert_called_once()

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_last_30_days_raw_data_failure(self, mock_engine):
        """Test failure case for raw data retrieval."""
        mock_engine.return_value.read_sql_query.side_effect = Exception("Database error")

        result = get_last_30_days_raw_data()
        assert result is None

    @patch('app.db.get_connection')
    def test_insert_prediction_success(self, mock_get_conn, sample_prediction_record):
        """Test successful prediction insertion."""
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1  # Simulate update
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Test
        insert_prediction(
            forecast_date="2025-12-11",
            predicted_level=13.2,
            flood_probability=0.1,
            days_ahead=1,
            lower_bound_80=12.8,
            upper_bound_80=13.6
        )

        # Verify
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_prediction_success(self, mock_engine):
        """Test successful prediction retrieval."""
        # Setup mock data
        data = {
            'predicted_level': [13.2],
            'lower_bound_80': [12.8],
            'upper_bound_80': [13.6],
            'flood_probability': [0.1],
            'days_ahead': [1],
            'date': ['2025-12-11'],
            'created_at': ['2025-12-10 12:00:00'],
        }
        df = pd.DataFrame(data)

        # Setup mock
        mock_read_sql = Mock(return_value=df)
        mock_engine.return_value.read_sql_query = mock_read_sql

        result = get_prediction("2025-12-11", 1)

        assert result is not None
        assert result['predicted_level'] == 13.2
        assert result['flood_probability'] == 0.1
        mock_read_sql.assert_called_once()

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_prediction_not_found(self, mock_engine):
        """Test prediction retrieval when not found."""
        # Setup empty mock data
        df = pd.DataFrame()
        mock_read_sql = Mock(return_value=df)
        mock_engine.return_value.read_sql_query = mock_read_sql

        result = get_prediction("2025-12-11", 1)

        assert result is None


class TestZoneOperations:
    """Test zone-related database operations."""

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_all_zones_success(self, mock_engine):
        """Test successful zone retrieval."""
        # Setup mock data
        data = {
            'zone_id': ['ZONE_001', 'ZONE_002'],
            'name': ['Downtown', 'West End'],
            'river_proximity': [0.9, 0.6],
            'elevation_risk': [0.3, 0.5],
            'pop_density': [0.8, 0.4],
            'crit_infra_score': [0.7, 0.3],
            'hospital_count': [2, 0],
            'critical_infra': [True, False],
        }
        df = pd.DataFrame(data)

        # Setup mock
        mock_read_sql = Mock(return_value=df)
        mock_engine.return_value.read_sql_query = mock_read_sql

        result = get_all_zones()

        assert len(result) == 2
        assert result[0]['zone_id'] == 'ZONE_001'
        assert result[0]['name'] == 'Downtown'

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_all_zones_empty(self, mock_engine):
        """Test zone retrieval with no data."""
        df = pd.DataFrame()
        mock_read_sql = Mock(return_value=df)
        mock_engine.return_value.read_sql_query = mock_read_sql

        result = get_all_zones()
        assert result == []

    @patch('app.db.get_connection')
    def test_insert_zone_success(self, mock_get_conn):
        """Test successful zone insertion."""
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Create zone insert data
        zone = ZoneInsert(
            zone_id="ZONE_001",
            name="Test Zone",
            river_proximity=0.8,
            elevation_risk=0.4,
            pop_density=0.6,
            crit_infra_score=0.5,
            hospital_count=1,
            critical_infra=False
        )

        # Test
        result = insert_zone(zone)

        # Verify
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


class TestResourceTypeOperations:
    """Test resource type-related database operations."""

    @patch('app.db.get_sqlalchemy_engine')
    def test_get_all_resource_types_success(self, mock_engine):
        """Test successful resource type retrieval."""
        # Setup mock data
        data = {
            'resource_id': ['R1_UAV', 'R2_ENGINEERING'],
            'name': ['UAV', 'Engineering'],
            'description': ['Test UAV', 'Test Engineering'],
            'icon': ['drone', 'engineering'],
            'display_order': [1, 2],
            'capacity': [5, 10],
        }
        df = pd.DataFrame(data)

        # Setup mock
        mock_read_sql = Mock(return_value=df)
        mock_engine.return_value.read_sql_query = mock_read_sql

        result = get_all_resource_types()

        assert len(result) == 2
        assert result[0]['resource_id'] == 'R1_UAV'
        assert result[0]['name'] == 'UAV'

    @patch('app.db.get_connection')
    def test_insert_resource_type_success(self, mock_get_conn):
        """Test successful resource type insertion."""
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Create resource type insert data
        resource = ResourceTypeInsert(
            resource_id="R1_UAV",
            name="UAV Surveillance",
            description="Test UAV",
            display_order=1,
            capacity=5
        )

        # Test
        result = insert_resource_type(resource)

        # Verify
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


class TestBatchOperations:
    """Test batch database operations."""

    @patch('app.db.get_connection')
    def test_insert_raw_data_batch_success(self, mock_get_conn):
        """Test successful raw data batch insertion."""
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Create test records
        records = [
            RawDataInsert(
                date=pd.Timestamp('2025-12-10'),
                daily_precip=0.1,
                target_level_max=10.0
            ),
            RawDataInsert(
                date=pd.Timestamp('2025-12-11'),
                daily_precip=0.2,
                target_level_max=10.5
            ),
            RawDataInsert(
                date=pd.Timestamp('2025-12-12'),
                daily_precip=0.15,
                target_level_max=11.0
            ),
        ]

        # Test
        result = insert_raw_data_batch(records)

        # Verify
        assert result == 3
        mock_cursor.executemany.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_insert_raw_data_batch_empty(self):
        """Test batch insertion with empty records."""
        result = insert_raw_data_batch([])
        assert result == 0


class TestTypedOperations:
    """Test typed database operations with Pydantic models."""

    @patch('app.db.get_all_resource_types')
    def test_get_all_resource_types_typed_success(self, mock_get_all):
        """Test successful typed resource type retrieval."""
        # Setup mock data
        mock_data = [
            {
                'resource_id': 'R1_UAV',
                'name': 'UAV Surveillance',
                'description': 'Test UAV',
                'icon': 'drone',
                'display_order': 1,
                'capacity': 5,
            }
        ]
        mock_get_all.return_value = mock_data

        # Test
        result = get_all_resource_types_typed()

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], ResourceType)
        assert result[0].resource_id == 'R1_UAV'
        assert result[0].name == 'UAV Surveillance'


class TestDataAccessObjects:
    """Test Data Access Object (DAO) classes."""

    def test_prediction_dao_create_from_dict(self):
        """Test PredictionDAO creation from dictionary."""
        data = {
            'forecast_date': '2025-12-11',
            'predicted_level': 13.2,
            'flood_probability': 0.1,
            'days_ahead': 1,
            'lower_bound_80': 12.8,
            'upper_bound_80': 13.6
        }

        prediction = PredictionDAO.create_from_dict(data)

        assert isinstance(prediction, PredictionInsert)
        assert prediction.forecast_date == '2025-12-11'
        assert prediction.predicted_level == 13.2

    def test_zone_dao_create_from_schema(self):
        """Test ZoneDAO creation from schema."""
        zone = Zone(
            zone_id="ZONE_001",
            name="Test Zone",
            pf=0.5,
            vulnerability=0.6,
            is_critical_infra=True,
            hospital_count=2,
            river_proximity=0.8,
            elevation_risk=0.4,
            pop_density=0.7,
            crit_infra_score=0.5
        )

        zone_insert = ZoneDAO.create_from_schema(zone)

        assert isinstance(zone_insert, ZoneInsert)
        assert zone_insert.zone_id == "ZONE_001"
        assert zone_insert.name == "Test Zone"
        assert zone_insert.river_proximity == 0.8

    def test_resource_type_dao_create_from_schema(self):
        """Test ResourceTypeDAO creation from schema."""
        resource = ResourceType(
            resource_id="R1_UAV",
            name="UAV Surveillance",
            description="Test UAV",
            icon="drone",
            display_order=1,
            capacity=5
        )

        resource_insert = ResourceTypeDAO.create_from_schema(resource)

        assert isinstance(resource_insert, ResourceTypeInsert)
        assert resource_insert.resource_id == "R1_UAV"
        assert resource_insert.name == "UAV Surveillance"
        assert resource_insert.capacity == 5

    def test_zone_dao_to_schema(self):
        """Test ZoneDAO conversion to schema."""
        record = {
            'zone_id': 'ZONE_001',
            'name': 'Test Zone',
            'river_proximity': 0.8,
            'elevation_risk': 0.4,
            'pop_density': 0.7,
            'crit_infra_score': 0.5,
            'hospital_count': 2,
            'critical_infra': True
        }

        zone = ZoneDAO.to_schema(record)

        assert isinstance(zone, Zone)
        assert zone.zone_id == 'ZONE_001'
        assert zone.name == 'Test Zone'
        assert zone.river_proximity == 0.8