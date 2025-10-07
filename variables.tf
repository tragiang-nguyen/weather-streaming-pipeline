variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "docker_image" {
  description = "Full Docker image name (without tag)"
  type        = string
  default     = "tragiang/weather-pipeline"
}