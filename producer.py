from kafka import KafkaProducer
import json
import requests
from datetime import datetime
import time
import os

bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")  # Mặc định là kafka:9092
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    request_timeout_ms=30000,
    retry_backoff_ms=500,
    max_block_ms=60000
)

API_KEY = "f552eba0452c41aa8cb82859252903"
CITY = "Hanoi"
URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=no"

def get_weather_data():
    response = requests.get(URL)
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
        return weather
    else:
        print(f"Error: {response.status_code}")
        return None

while True:
    weather_data = get_weather_data()
    if weather_data:
        producer.send('weather_data', weather_data)
        print(f"Sent: {weather_data}")
    time.sleep(10)
producer.flush()

print("Weather data streaming started.")