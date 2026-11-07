terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.0"
    }
  }
}

# Configures the provider to use your local Docker Desktop daemon
provider "docker" {}

# Simulates fetching a machine image (like an Azure Compute Gallery image)
resource "docker_image" "nginx" {
  name         = "nginx:latest"
  keep_locally = false
}

# Simulates provisioning a Virtual Machine
resource "docker_container" "web_server" {
  image = docker_image.nginx.image_id
  name  = "phase1_local_web"
  
  ports {
    internal = 80
    external = 8080
  }
}