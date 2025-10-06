terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23.0"
    }
  }
}

provider "docker" {}

provider "kubernetes" {
  config_path = "~/.kube/config" # Path đến kubeconfig của minikube
}

resource "docker_volume" "kafka_data" {
  name = "kafka_data"
}

resource "kubernetes_namespace" "weather" {
  metadata {
    name = "weather"
  }
}

resource "kubernetes_deployment" "zookeeper" {
  metadata {
    name      = "zookeeper"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "zookeeper"
      }
    }
    template {
      metadata {
        labels = {
          app = "zookeeper"
        }
      }
      spec {
        container {
          image = "zookeeper:3.9.2"
          name  = "zookeeper"
          port {
            container_port = 2181
          }
          env {
            name  = "ALLOW_ANONYMOUS_LOGIN"
            value = "yes"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "zookeeper_service" {
  metadata {
    name      = "zookeeper-service"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    selector = {
      app = "zookeeper"
    }
    port {
      protocol    = "TCP"
      port        = 2181
      target_port = 2181
    }
  }
}

resource "kubernetes_deployment" "kafka" {
  metadata {
    name      = "kafka"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "kafka"
      }
    }
    template {
      metadata {
        labels = {
          app = "kafka"
        }
      }
      spec {
        container {
          image = "confluentinc/cp-kafka:7.5.0"
          name  = "kafka"
          port {
            container_port = 9092
          }
          env {
            name  = "KAFKA_ADVERTISED_LISTENERS"
            value = "PLAINTEXT://kafka-service:9092"
          }
          env {
            name  = "KAFKA_LISTENERS"
            value = "PLAINTEXT://0.0.0.0:9092"
          }
          env {
            name  = "KAFKA_ZOOKEEPER_CONNECT"
            value = "zookeeper-service:2181"
          }
          env {
            name  = "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR"
            value = "1"
          }
          env {
            name  = "ALLOW_PLAINTEXT_LISTENER"
            value = "yes"
          }
          env {
            name  = "KAFKA_BROKER_ID"
            value = "1"
          }
          volume_mount {
            name       = "kafka-data"
            mount_path = "/bitnami/kafka/data"
          }
        }
        volume {
          name = "kafka-data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "kafka_service" {
  metadata {
    name      = "kafka-service"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    selector = {
      app = "kafka"
    }
    port {
      protocol    = "TCP"
      port        = 9092
      target_port = 9092
    }
  }
}

resource "kubernetes_deployment" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "postgres"
      }
    }
    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }
      spec {
        container {
          image = "postgres:latest"
          name  = "postgres"
          port {
            container_port = 5432
          }
          env {
            name  = "POSTGRES_USER"
            value = "postgres"
          }
          env {
            name  = "POSTGRES_DB"
            value = "weather_db"
          }
          env {
            name  = "POSTGRES_HOST_AUTH_METHOD"
            value = "trust"
          }
          volume_mount {
            name       = "postgres-config"
            mount_path = "/etc/postgresql/pg_hba.conf"
            sub_path   = "pg_hba.conf"
          }
        }
        volume {
          name = "postgres-config"
          config_map {
            name = kubernetes_config_map.postgres_config.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_config_map" "postgres_config" {
  metadata {
    name      = "postgres-config"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  data = {
    "pg_hba.conf" = "local all all trust\nhost all all 0.0.0.0/0 trust"
  }
}

resource "kubernetes_service" "postgres_service" {
  metadata {
    name      = "postgres-service"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    selector = {
      app = "postgres"
    }
    port {
      protocol    = "TCP"
      port        = 5432
      target_port = 5432
    }
  }
}

resource "kubernetes_deployment" "weather_pipeline" {
  metadata {
    name      = "weather-pipeline"
    namespace = kubernetes_namespace.weather.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "weather-pipeline"
      }
    }
    template {
      metadata {
        labels = {
          app = "weather-pipeline"
        }
      }
      spec {
        container {
          image             = "weather-pipeline:latest"
          image_pull_policy = "IfNotPresent"
          name              = "weather-pipeline"
          command           = ["/bin/bash", "-c"]
          args              = [
            "python3 /app/producer.py & python3 /opt/spark/work-dir/streaming_pipeline.py"
          ]
          env {
            name  = "JDBC_URL"
            value = "jdbc:postgresql://postgres-service:5432/weather_db"
          }
          env {
            name  = "JDBC_USER"
            value = "postgres"
          }
          env {
            name  = "KAFKA_BOOTSTRAP_SERVERS"
            value = "kafka-service:9092"
          }
          volume_mount {
            name       = "checkpoint-volume"
            mount_path = "/opt/spark/checkpoint"
          }
        }
        volume {
          name = "checkpoint-volume"
          empty_dir {}
        }
      }
    }
  }
}