# Ống Dữ Liệu Thời Gian Thực Thời Tiết (Realtime Weather Data Pipeline)

## Tổng Quan
Dự án này triển khai một đường ống dữ liệu thời gian thực mô phỏng GCP Dataflow và Cloud Pub/Sub bằng Apache Kafka (để thu thập dữ liệu) và Spark Structured Streaming (để xử lý). Nó xử lý khoảng 10.000 điểm dữ liệu thời tiết mỗi phút từ API giả lập, tổng hợp trung bình hàng giờ (nhiệt độ, độ ẩm, tốc độ gió) với watermarking cho dữ liệu muộn, và ghi vào PostgreSQL. Hệ thống chịu lỗi với checkpointing, được container hóa bằng Docker, triển khai trên Kubernetes (Minikube), và quản lý bằng Terraform. Hiệu suất được tối ưu hóa với indexing PostgreSQL (query <5ms).

Các tính năng chính:
- **Thu thập dữ liệu**: Producer Kafka gửi dữ liệu thời tiết (JSON) vào topic `weather_data`.
- **Xử lý**: Spark tổng hợp dữ liệu trong cửa sổ 1 giờ, xử lý dữ liệu muộn với watermark 10 phút.
- **Lưu trữ**: PostgreSQL với bảng được index để query nhanh.
- **Mở rộng & Chịu lỗi**: Triển khai Kubernetes, PVC cho checkpoint.
- **Tests**: Pytest bao phủ logic producer và streaming (4/4 passed).

## Yêu Cầu Hệ Thống
- Ubuntu/WSL2 với Docker, Minikube, kubectl, Terraform đã cài đặt.
- Python 3.10+ với virtualenv (cho tests).
- Tài khoản Docker Hub (tùy chọn, cho CI/CD push).

## Hướng Dẫn Nhanh
Clone và chạy trong ~20-30 phút.

### 1. Clone Repository
```bash
git clone <repo-url> realtime-pipeline
cd realtime-pipeline
```

### 2. Thiết Lập Môi Trường (Tests)
```bash
python3 -m venv stock_test_env
source stock_test_env/bin/activate  # Trên Windows: stock_test_env\Scripts\activate
pip install pytest kafka-python requests pyspark==3.5.0 pytest-cov
```

### 3. Chạy Tests
```bash
PYTHONPATH=. pytest tests/ -v
```
- Kết quả mong đợi: 4 tests passed (2 producer, 2 streaming).

### 4. Khởi Động Minikube
```bash
minikube start --driver=docker --cpus=4 --memory=4096mb
kubectl config use-context minikube
```

### 5. Pull Images Cơ Bản
```bash
minikube image pull zookeeper:3.9.2
minikube image pull confluentinc/cp-kafka:7.5.0
minikube image pull postgres:latest
```

### 6. Build và Load Image Docker
```bash
docker build --no-cache -t weather-pipeline:latest .
minikube image load weather-pipeline:latest
```

### 7. Triển Khai Với Terraform
```bash
terraform init
terraform apply  # Nhập 'yes'
```
- Chờ 5-10 phút rollout (kiểm tra `kubectl get pods -n weather`).

### 8. Tạo Bảng PostgreSQL (Nếu Chưa Có)
```bash
kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "
CREATE TABLE IF NOT EXISTS weather_summary (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    avg_temp DOUBLE PRECISION,
    avg_humidity DOUBLE PRECISION,
    avg_wind_speed DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_window_start ON weather_summary (window_start);
"
```

### 9. Theo Dõi Log
```bash
kubectl -n weather logs -f deployment/weather-pipeline --timestamps
```
- Thấy "Sent: {...}" (producer), "Batch {id}:" (aggregation), hiển thị dữ liệu, write OK.
- Chờ 5 phút để thấy batch chạy.

### 10. Xác Nhận Dữ Liệu
```bash
kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "SELECT COUNT(*) FROM weather_summary;"
```
- Số lượng tăng dần (ví dụ: từ 0 lên 3+).

Test hiệu suất query (<5ms):
```bash
kubectl -n weather exec -it deployment/postgres -- psql -U postgres -d weather_db -c "EXPLAIN ANALYZE SELECT * FROM weather_summary WHERE window_start > NOW() - INTERVAL '1 hour';"
```
- Execution Time <5ms.

## Kiến Trúc
- **Producer**: Script Python gửi dữ liệu thời tiết (API/mock) vào Kafka mỗi 0.006s (~10k/phút).
- **Spark Streaming**: Đọc Kafka, parse JSON, tổng hợp trung bình hàng giờ, ghi vào Postgres.
- **Lưu trữ**: Postgres với bảng được index.
- **Cơ Sở Hạ Tầng**: Terraform triển khai tài nguyên K8s (deployments, services, PVC).
- **Mở Rộng**: Replicas=1 (scale với `kubectl scale --replicas=3 deployment/weather-pipeline -n weather`).

## Các File
- **producer.py**: Producer Kafka với dữ liệu API/mock.
- **streaming_pipeline.py**: Logic Spark streaming (aggregation, write).
- **Dockerfile**: Build image với Spark, libs Kafka, producer/streaming.
- **main.tf**: Terraform cho K8s (namespace, deployments, services, PVC).
- **tests/test_producer.py**: Mock API/Kafka cho tests producer.
- **tests/test_streaming.py**: Mock DataFrame/Spark cho tests streaming.

## Dọn Dẹp
```bash
kubectl -n weather scale deployment/weather-pipeline --replicas=0  # Dừng pipeline
terraform destroy -auto-approve
minikube stop
```

## Khắc Phục Sự Cố
- **NoBrokersAvailable**: Chờ 1 phút (Kafka khởi động).
- **Jar missing**: Rebuild Docker image.
- **Pod not Ready**: `kubectl describe pod <pod-name> -n weather`.
- **Tests fail**: Đảm bảo PYTHONPATH=. và venv activated.
