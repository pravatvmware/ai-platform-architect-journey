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


# Generated Container: frontend_node_dev
resource "docker_container" "frontend_node_dev" {
  image = docker_image.app_image.image_id
  name  = "frontend_node_dev"
  
  ports {
    internal = 80
    external = 8081
  }
}
