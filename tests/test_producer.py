import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Thêm thư mục cha

from unittest.mock import patch, Mock
from producer import get_weather_data

@patch('producer.KafkaProducer')  # Patch theo module producer
@patch('requests.get')
def test_get_weather_data_success(mock_get, mock_kafka):
    # Mock KafkaProducer return một Mock object
    mock_prod = Mock()
    mock_kafka.return_value = mock_prod

    # Mock response thành công
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {
            "temp_c": 25.0,
            "humidity": 94,
            "wind_kph": 6.1,
            "condition": {"text": "Mist"},
            "last_updated": "2025-08-27 22:00"
        }
    }
    mock_get.return_value = mock_response

    result = get_weather_data()
    assert result is not None
    assert result['city'] == 'Hanoi'
    assert result['temperature_c'] == 25.0
    assert result['humidity'] == 94
    assert 'condition' in result
    assert 'timestamp' in result
    mock_kafka.assert_called_once()  # Kiểm tra mock được gọi

@patch('producer.KafkaProducer')
@patch('requests.get')
def test_get_weather_data_error(mock_get, mock_kafka):
    mock_prod = Mock()
    mock_kafka.return_value = mock_prod

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_weather_data()
    assert result is None
    mock_kafka.assert_not_called()  # Mock không được gọi vì skip if
