from kafka import KafkaProducer
import json
import requests
from datetime import datetime
import time
import os

bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
producer = None  # Khởi tạo lazy

def get_kafka_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=30000,
            retry_backoff_ms=500,
            max_block_ms=60000
        )
    return producer

API_KEY = "f552eba0452c41aa8cb82859252903"
CITY = "Hanoi"
URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=no"

def get_weather_data():
    try:
        response = requests.get(URL, timeout=10)  # Thêm timeout 10s
        if response.status_code == 200:
            data = response.json()
            weather = {
                "city": CITY,
                "temperature_c": data["current"]["temp_c"],
                "humidity": data["current"]["humidity"],
                "wind_speed_kph": data["current"]["wind_kph"],
                "condition": data["current"]["condition"]["text"],
                "last_updated": data["current"]["last_updated"],
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            raise Exception(f"API error: {response.status_code}")
    except Exception as e:
        print(f"API timeout or error: {e}. Using mock data.")
        # Mock data nếu API fail
        weather = {
            "city": CITY,
            "temperature_c": 25.0 + time.time() % 10,  # Giá trị thay đổi nhẹ
            "humidity": 94,
            "wind_speed_kph": 7.2,
            "condition": "Sunny",
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # Gửi vào Kafka
    prod = get_kafka_producer()
    prod.send('weather_data', weather)
    print(f"Sent: {weather}")
    return weather

if __name__ == "__main__":
    while True:
        weather_data = get_weather_data()
        if weather_data:
            time.sleep(0.006)  # ~10k/phút
    producer.flush()
    print("Weather data streaming started.")