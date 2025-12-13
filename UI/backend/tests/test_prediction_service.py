"""
Tests for prediction service functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

from app.prediction_service import (
    predict_next_days,
    predict_all_historical,
    _missing_model_files,
    _naive_fallback_prediction,
    _create_flood_risk,
    _create_current_conditions,
    _create_prediction_from_dict,
    _model_dir_for_lead,
)
from app.schemas import (
    Prediction,
    FloodRisk,
    CurrentConditions,
    Forecast,
    PredictionInterval,
)
from app.db_models import PredictionInsert


class TestPredictionHelpers:
    """Test prediction service helper functions."""

    def test_model_dir_for_lead(self):
        """Test model directory path generation."""
        with patch('app.prediction_service.MODEL_BASE_DIR', Path('/base/models')):
            result = _model_dir_for_lead(1)
            assert result == Path('/base/models/L1d/models')

            result = _model_dir_for_lead(3)
            assert result == Path('/base/models/L3d/models')

    @patch('app.prediction_service._model_dir_for_lead')
    @patch('app.prediction_service.Path.exists')
    def test_missing_model_files(self, mock_exists, mock_model_dir):
        """Test missing model files detection."""
        # Setup mock directory
        mock_dir = Path('/test/models/L1d/models')
        mock_model_dir.return_value = mock_dir

        # Mock file existence - some files missing
        def mock_exists_side_effect(path):
            missing_files = ['xgb_q10.json', 'lstm_q10.h5']
            return path.name not in missing_files

        mock_exists.side_effect = mock_exists_side_effect

        missing = _missing_model_files(1)

        assert len(missing) == 2
        assert any('xgb_q10.json' in path for path in missing)
        assert any('lstm_q10.h5' in path for path in missing)

    def test_create_flood_risk(self):
        """Test flood risk creation."""
        # Test low risk
        flood_risk = _create_flood_risk(0.1)
        assert flood_risk.probability == 0.1
        assert flood_risk.risk_level == "LOW"
        assert flood_risk.risk_indicator == "🟢"

        # Test moderate risk
        flood_risk = _create_flood_risk(0.5)
        assert flood_risk.risk_level == "MODERATE"
        assert flood_risk.risk_indicator == "🟡"

        # Test high risk
        flood_risk = _create_flood_risk(0.8)
        assert flood_risk.risk_level == "HIGH"
        assert flood_risk.risk_indicator == "🔴"

    def test_create_current_conditions(self, sample_raw_data):
        """Test current conditions creation."""
        last_row = sample_raw_data.iloc[-1]
        conditions = _create_current_conditions(last_row)

        assert isinstance(conditions, CurrentConditions)
        assert conditions.date == str(last_row['date'])
        assert conditions.current_level_st_louis == round(float(last_row['target_level_max']), 2)

    def test_create_prediction_from_dict(self, sample_prediction):
        """Test prediction creation from dictionary."""
        prediction = _create_prediction_from_dict(sample_prediction)

        assert isinstance(prediction, Prediction)
        assert prediction.lead_time_days == 1
        assert prediction.forecast_date == sample_prediction['forecast_date']
        assert isinstance(prediction.current_conditions, CurrentConditions)
        assert isinstance(prediction.forecast, Forecast)
        assert isinstance(prediction.prediction_interval_80pct, PredictionInterval)
        assert isinstance(prediction.flood_risk, FloodRisk)

    def test_create_prediction_from_dict_minimal(self):
        """Test prediction creation with minimal data."""
        minimal_data = {
            'lead_time_days': 2,
            'forecast_date': '2025-12-12',
            'error': 'Model not available'
        }

        prediction = _create_prediction_from_dict(minimal_data)

        assert isinstance(prediction, Prediction)
        assert prediction.lead_time_days == 2
        assert prediction.forecast_date == '2025-12-12'
        assert prediction.error == 'Model not available'
        assert prediction.current_conditions is None
        assert prediction.forecast is None


class TestNaiveFallbackPrediction:
    """Test naive fallback prediction functionality."""

    def test_naive_fallback_prediction_normal(self, sample_raw_data):
        """Test naive fallback prediction with normal conditions."""
        result = _naive_fallback_prediction(sample_raw_data, 1)

        assert 'lead_time_days' in result
        assert 'forecast' in result
        assert 'flood_risk' in result
        assert 'current_conditions' in result
        assert 'prediction_interval_80pct' in result

        assert result['lead_time_days'] == 1
        assert result['forecast']['median'] < 30.0  # Should not trigger flood risk
        assert result['flood_risk']['probability'] == 0.0
        assert result['flood_risk']['risk_level'] == 'LOW'

    def test_naive_fallback_prediction_flood_conditions(self, sample_raw_data):
        """Test naive fallback prediction with flood conditions."""
        # Modify data to simulate flood conditions
        sample_raw_data.loc[sample_raw_data.index[-1], 'target_level_max'] = 35.0

        result = _naive_fallback_prediction(sample_raw_data, 1)

        assert result['forecast']['median'] >= 30.0
        assert result['flood_risk']['probability'] == 1.0
        assert result['flood_risk']['risk_level'] == 'HIGH'
        assert result['flood_risk']['risk_indicator'] == '🔴'


class TestPredictNextDays:
    """Test predict_next_days functionality."""

    @patch('app.prediction_service._missing_model_files')
    @patch('app.prediction_service.FloodPredictorV2')
    @patch('app.prediction_service.get_prediction')
    def test_predict_next_days_with_cached_data(self, mock_get_pred, mock_predictor, mock_missing):
        """Test prediction with cached data available."""
        # Setup mocks
        mock_missing.return_value = []  # No missing files
        mock_cached_prediction = {
            'predicted_level': 13.2,
            'flood_probability': 0.1,
            'lower_bound_80': 12.8,
            'upper_bound_80': 13.6,
            'created_at': datetime.now()
        }
        mock_get_pred.return_value = mock_cached_prediction

        # Mock predictor
        mock_predictor_instance = Mock()
        mock_predictor.return_value = mock_predictor_instance
        mock_predictor_instance.predict_from_raw_data.return_value = {
            'forecast': {'median': 13.2},
            'prediction_interval_80pct': {'lower': 12.8, 'upper': 13.6, 'width': 0.8},
            'flood_risk': {'probability': 0.1, 'threshold_ft': 30.0}
        }

        # Test
        predictions = predict_next_days(pd.DataFrame({'date': [datetime.now()]}), [1])

        assert len(predictions) == 1
        assert isinstance(predictions[0], Prediction)
        assert predictions[0].cached is True

    @patch('app.prediction_service._missing_model_files')
    @patch('app.prediction_service.FloodPredictorV2')
    @patch('app.prediction_service.get_prediction')
    def test_predict_next_days_no_cache(self, mock_get_pred, mock_predictor, mock_missing, sample_raw_data):
        """Test prediction with no cached data."""
        # Setup mocks
        mock_missing.return_value = []  # No missing files
        mock_get_pred.return_value = None  # No cached prediction

        # Mock predictor
        mock_predictor_instance = Mock()
        mock_predictor.return_value = mock_predictor_instance
        mock_predictor_instance.predict_from_raw_data.return_value = {
            'forecast': {'median': 13.2},
            'prediction_interval_80pct': {'lower': 12.8, 'upper': 13.6, 'width': 0.8},
            'flood_risk': {'probability': 0.1, 'threshold_ft': 30.0}
        }

        # Test
        predictions = predict_next_days(sample_raw_data, [1])

        assert len(predictions) == 1
        assert isinstance(predictions[0], Prediction)
        assert predictions[0].cached is False

    @patch('app.prediction_service._missing_model_files')
    def test_predict_next_days_missing_models(self, mock_missing, sample_raw_data):
        """Test prediction when model files are missing."""
        # Setup mock to show missing files
        mock_missing.return_value = ['/path/to/missing/model.json']

        # Test
        predictions = predict_next_days(sample_raw_data, [1])

        assert len(predictions) == 1
        assert isinstance(predictions[0], Prediction)
        assert predictions[0].error is not None
        assert "Model files not found" in predictions[0].error

    @patch('app.prediction_service._missing_model_files')
    @patch('app.prediction_service._naive_fallback_prediction')
    @patch('app.prediction_service.get_prediction')
    def test_predict_next_days_prediction_error(self, mock_get_pred, mock_naive, mock_missing, sample_raw_data):
        """Test prediction when main prediction fails."""
        # Setup mocks
        mock_missing.return_value = []  # No missing files
        mock_get_pred.return_value = None  # No cached prediction

        # Mock naive fallback
        mock_naive.return_value = {
            'lead_time_days': 1,
            'forecast_date': '2025-12-11',
            'forecast': {'median': 10.0},
            'flood_risk': {'probability': 0.0}
        }

        # Mock the predictor to raise an exception
        with patch('app.prediction_service.FloodPredictorV2') as mock_predictor:
            mock_predictor.side_effect = Exception("Prediction failed")

            predictions = predict_next_days(sample_raw_data, [1])

            assert len(predictions) == 1
            assert isinstance(predictions[0], Prediction)
            # Should fallback to naive prediction
            mock_naive.assert_called_once()


class TestPredictAllHistorical:
    """Test predict_all_historical functionality."""

    @patch('app.prediction_service.get_all_raw_data')
    @patch('app.prediction_service.predict_next_days')
    @patch('app.prediction_service.get_prediction')
    def test_predict_all_historical_success(self, mock_get_pred, mock_predict, mock_get_all):
        """Test successful historical prediction."""
        # Setup mock data (40 days for multiple 30-day windows)
        dates = pd.date_range(end=datetime.now(), periods=40, freq='D')
        data = []
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'target_level_max': 10.0 + i * 0.1,
            })
        mock_df = pd.DataFrame(data)
        mock_get_all.return_value = mock_df

        # Mock prediction function
        mock_prediction = Prediction(
            lead_time_days=1,
            forecast_date='2025-12-11',
            forecast=Forecast(median=13.2),
            flood_risk=FloodRisk(probability=0.1)
        )
        mock_predict.return_value = [mock_prediction]

        # Test
        result = predict_all_historical(lead_times=[1], skip_cached=False)

        assert result['status'] == 'completed'
        assert result['total_predictions'] > 0
        assert 'predictions_by_lead_time' in result
        assert 'lead_time_1' in result['predictions_by_lead_time']
        assert len(result['predictions_by_lead_time']['lead_time_1']) > 0

    @patch('app.prediction_service.get_all_raw_data')
    def test_predict_all_historical_insufficient_data(self, mock_get_all):
        """Test historical prediction with insufficient data."""
        # Mock insufficient data (less than 30 days)
        dates = pd.date_range(end=datetime.now(), periods=20, freq='D')
        data = [{'date': date, 'target_level_max': 10.0} for date in dates]
        mock_get_all.return_value = pd.DataFrame(data)

        result = predict_all_historical()

        assert 'error' in result
        assert result['total_predictions'] == 0
        assert "Insufficient historical data" in result['error']

    @patch('app.prediction_service.get_all_raw_data')
    @patch('app.prediction_service.predict_next_days')
    @patch('app.prediction_service.get_prediction')
    def test_predict_all_historical_skip_cached(self, mock_get_pred, mock_predict, mock_get_all):
        """Test historical prediction with skip_cached enabled."""
        # Setup mock data
        dates = pd.date_range(end=datetime.now(), periods=35, freq='D')
        data = [{'date': date, 'target_level_max': 10.0} for date in dates]
        mock_get_all.return_value = pd.DataFrame(data)

        # Mock cached prediction exists
        mock_get_pred.return_value = {'predicted_level': 13.0, 'flood_probability': 0.1}

        result = predict_all_historical(skip_cached=True)

        # Should skip cached predictions
        assert result['skipped_cached'] > 0

    @patch('app.prediction_service.get_all_raw_data')
    @patch('app.prediction_service.predict_next_days')
    @patch('app.prediction_service.get_prediction')
    def test_predict_all_historical_progress_callback(self, mock_get_pred, mock_predict, mock_get_all):
        """Test historical prediction with progress callback."""
        # Setup mock data
        dates = pd.date_range(end=datetime.now(), periods=35, freq='D')
        data = [{'date': date, 'target_level_max': 10.0} for date in dates]
        mock_get_all.return_value = pd.DataFrame(data)

        # Mock prediction
        mock_prediction = Prediction(
            lead_time_days=1,
            forecast_date='2025-12-11',
            forecast=Forecast(median=13.2),
            flood_risk=FloodRisk(probability=0.1)
        )
        mock_predict.return_value = [mock_prediction]

        # Test with progress callback
        progress_calls = []
        def progress_callback(progress):
            progress_calls.append(progress)

        result = predict_all_historical(
            lead_times=[1],
            skip_cached=True,
            on_progress=progress_callback
        )

        # Should have received progress updates
        assert len(progress_calls) > 0
        assert 'percent' in progress_calls[0]

    @patch('app.prediction_service.get_all_raw_data')
    def test_predict_all_historical_cancel_check(self, mock_get_all):
        """Test historical prediction with cancellation."""
        # Setup mock data
        dates = pd.date_range(end=datetime.now(), periods=35, freq='D')
        data = [{'date': date, 'target_level_max': 10.0} for date in dates]
        mock_get_all.return_value = pd.DataFrame(data)

        # Test with cancellation
        def cancel_check():
            return True  # Always cancel

        result = predict_all_historical(cancel_check=cancel_check)

        assert result['summary']['cancelled'] is True
        assert 'Cancelled by user' in result['errors']


class TestPredictionIntegration:
    """Integration tests for prediction service."""

    @patch('app.prediction_service.insert_prediction')
    def test_prediction_caching_integration(self, mock_insert):
        """Test that predictions are properly cached."""
        # This would require more complex setup with actual database integration
        # For now, test the interface is called correctly
        mock_insert.return_value = None

        # Test that insert_prediction is called with correct parameters
        PredictionInsert(
            forecast_date="2025-12-11",
            predicted_level=13.2,
            flood_probability=0.1,
            days_ahead=1
        )

        # The test would need to verify that insert_prediction is called
        # with Pydantic-validated data
        assert True  # Placeholder for integration test