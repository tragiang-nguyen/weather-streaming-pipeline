terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
  }
}
provider "docker" {}
resource "docker_volume" "kafka_data" {
  name = "kafka_data"
}
resource "docker_container" "kafka" {
  name = "kafka"
  image = "bitnami/kafka:2.8"
  ports {
    internal = 9092
    external = 9092
  }
  env = [
    "KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092",
    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1",
    "KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181",
    "KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092",
    "KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT",
    "KAFKA_BROKER_ID=1",
    "KAFKA_HEAP_OPTS=-Xms512m -Xmx512m",
    "KAFKA_ADVERTISED_HOST_NAME=localhost",
    "KAFKA_ADVERTISED_PORT=9092",
    "ALLOW_PLAINTEXT_LISTENER=yes"
  ]
  volumes {
    volume_name = docker_volume.kafka_data.name
    container_path = "/bitnami/kafka/data"
  }
  networks_advanced {
    name = "kafka_network"
  }
  depends_on = [docker_container.zookeeper]
}
resource "docker_container" "zookeeper" {
  name = "zookeeper"
  image = "bitnami/zookeeper:latest"
  ports {
    internal = 2181
    external = 2181
  }
  env = [
    "ALLOW_ANONYMOUS_LOGIN=yes"
  ]
  networks_advanced {
    name = "kafka_network"
  }
}
resource "docker_container" "postgres" {
  name = "postgres"
  image = "postgres:latest"
  ports {
    internal = 5432
    external = 5432
  }
  env = [
    "POSTGRES_USER=postgres",
    "POSTGRES_PASSWORD=postgres",
    "POSTGRES_DB=weather_db"
  ]
  networks_advanced {
    name = "db_network"
  }
}
resource "docker_network" "kafka_network" {
  name = "kafka_network"
}
resource "docker_network" "db_network" {
  name = "db_network"
}