# Weather Data Streaming Pipeline

Thiết kế và triển khai hệ thống pipeline dữ liệu thời gian thực mô phỏng GCP Dataflow và Cloud Pub/Sub, sử dụng Apache Kafka làm broker và Spark Structured Streaming để xử lý dữ liệu với tốc độ mục tiêu 10.000 bản ghi mỗi phút. Hệ thống được container hóa bằng Docker, triển khai trên Kubernetes (Minikube), quản lý hạ tầng bằng Terraform, và đảm bảo khả năng mở rộng/chịu lỗi qua checkpointing. Tối ưu hóa hiệu suất với indexing PostgreSQL, giảm thời gian query xuống dưới 5ms trên bảng trống.

## Prerequisites

- **Docker**: Đảm bảo Docker Desktop đã được cài đặt và chạy.
- **Kubernetes**: Cài đặt Minikube hoặc một cụm Kubernetes.
- **Terraform**: Cài đặt Terraform để quản lý hạ tầng.
- **API Key**: Đăng ký tại [WeatherAPI](https://www.weatherapi.com/) để lấy API key và cập nhật trong `producer.py` (hiện tại là `f552eba0452c41aa8cb82859252903`).
- **Python**: Đã cài đặt Python 3.x với thư viện `kafka-python` và `requests`.

## Project Structure

```
realtime-pipeline/
├── .git/
├── .terraform/
├── jars/              # Thư mục chứa các JAR file (Spark SQL Kafka, PostgreSQL, v.v.)
├── postgres-config/   # Cấu hình PostgreSQL
├── docker-compose.yml # Cấu hình Docker Compose
├── Dockerfile         # File Docker để build image producer
├── main.tf            # Cấu hình Terraform
├── producer.py        # Script Python để sản xuất dữ liệu thời tiết
├── streaming_pipeline.py # Script Spark để xử lý dữ liệu
├── spark-deployment.yaml # Cấu hình Kubernetes
├── terraform.tfstate  # Trạng thái Terraform
└── terraform.tfstate.backup
```

## Installation and Setup

### 1. Cài Đặt Môi Trường
1. Cài đặt Kafka và Zookeeper:
   - Tải từ https://kafka.apache.org/downloads.
   - Chạy Zookeeper: `bin/zookeeper-server-start.sh config/zookeeper.properties`.
   - Chạy Kafka: `bin/kafka-server-start.sh config/server.properties`.
   - Kiểm tra: Tạo topic `transactions` bằng `bin/kafka-topics.sh --create --topic transactions --bootstrap-server localhost:9092`.

2. Cài đặt Spark và PySpark:
   - Tải Spark từ https://spark.apache.org/downloads.html.
   - Cài PySpark: `pip install pyspark==3.5.0`.
   - Thêm JAR cho Kafka integration: Tải `spark-sql-kafka-0-10_2.12:3.5.0` từ Maven và config trong SparkSession.

3. Cài đặt PostgreSQL:
   - Cài qua package manager (e.g., `sudo apt install postgresql` trên Ubuntu).
   - Tạo database `transactions` và table `revenue_summary` (cột: product STRING, total_revenue DOUBLE).
   - Kiểm tra: Kết nối bằng `psql` và chạy query tạo table.

4. Cài đặt Docker, Minikube, Terraform và Git:
   - Docker: Theo hướng dẫn https://docs.docker.com/get-docker/.
   - Minikube: `curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube`.
   - Terraform: Tải từ https://www.terraform.io/downloads.
   - Git: `sudo apt install git`.
   - Kiểm tra: Chạy `docker --version`, `minikube version`, `terraform --version`, `git --version`.

## 2. Chạy dự án
wsl --list --all

cd D:\projects\realtime-pipeline

wsl -d Ubuntu-D -u user

minikube stop

minikube delete

minikube start --driver=docker

minikube status

kubectl get nodes

minikube image build -t weather-pipeline:latest .

terraform init

terraform apply

kubectl get namespaces

kubectl -n weather get deployments

kubectl -n weather get services

kubectl -n weather get pods

kubectl -n weather exec -it deployment/kafka -- /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-service:9092 --topic weather_data --from-beginning

kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "TRUNCATE TABLE weather_summary;"

kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "CREATE INDEX idx_window_start ON weather_summary (window_start);"

kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "SELECT * FROM weather_summary;"

kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "\timing on" -c "SELECT * FROM weather_summary WHERE window_start = '2025-08-27 15:00:00';"

## Nếu lỗi
docker run -it --rm --network kafka_network -v kafka_data:bitnami/kafka/data bitnami/kafka:2.8 bash

cd /bitnami/kafka/data

echo "broker.id=1" > meta.properties

echo "listeners=PLAINTEXT://:9092" >> meta.properties

cat meta.properties

exit

terraform validate

terraform init

terraform apply

docker ps -a

docker exec -it postgres psql -U postgres -d weather_db

CREATE TABLE weather_summary (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    avg_temp DOUBLE PRECISION,
    avg_humidity DOUBLE PRECISION,
    avg_wind_speed DOUBLE PRECISION
);

\dt

exit
