terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.0"
    }
  }
}

provider "docker" {}

# Dynamically fetch the base image from config
resource "docker_image" "app_image" {
  name         = "nginx:latest"
  keep_locally = false
}


# Generated Container: frontend_node
resource "docker_container" "frontend_node" {
  image = docker_image.app_image.image_id
  name  = "frontend_node"
  
  ports {
    internal = 80
    external = 8081
  }
}

# Generated Container: backend_api_node
resource "docker_container" "backend_api_node" {
  image = docker_image.app_image.image_id
  name  = "backend_api_node"
  
  ports {
    internal = 80
    external = 8082
  }
}
