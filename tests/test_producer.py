import pytest
from unittest.mock import Mock, patch
from kafka import KafkaProducer

# Absolute import (from parent dir)
from producer import get_weather_data, get_kafka_producer

class TestProducer:
    @patch('requests.get')
    def test_producer_sends_data(self, mock_get):
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current": {
                "temp_c": 25.0,
                "humidity": 80,
                "wind_kph": 10.5,
                "condition": {"text": "Sunny"},
                "last_updated": "2023-10-07 10:00"
            }
        }
        mock_get.return_value = mock_response

        # Mock KafkaProducer
        with patch('producer.get_kafka_producer') as mock_producer:
            mock_prod = Mock(spec=KafkaProducer)
            mock_producer.return_value = mock_prod
            mock_prod.send.return_value = None

            # Call function
            weather = get_weather_data()

            # Assertions
            assert weather["city"] == "Hanoi"
            assert weather["temperature_c"] == 25.0
            assert weather["humidity"] == 80
            mock_prod.send.assert_called_once_with('weather_data', weather)

    @patch('requests.get')
    def test_producer_handles_api_error(self, mock_get):
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Mock KafkaProducer
        with patch('producer.get_kafka_producer') as mock_producer:
            mock_prod = Mock(spec=KafkaProducer)
            mock_producer.return_value = mock_prod
            mock_prod.send.return_value = None

            # Call function
            weather = get_weather_data()

            # Assertions (mock data)
            assert weather["city"] == "Hanoi"
            assert weather["temperature_c"] > 0  # Mock temp > 0
            assert weather["condition"] == "Sunny"
            mock_prod.send.assert_called_once_with('weather_data', weather)