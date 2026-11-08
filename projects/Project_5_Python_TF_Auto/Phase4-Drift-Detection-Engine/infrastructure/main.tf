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


# Generated Container: frontend_node_prod_1
resource "docker_container" "frontend_node_prod_1" {
  image = docker_image.app_image.image_id
  name  = "frontend_node_prod_1"
  
  ports {
    internal = 80
    external = 8081
  }
}

# Generated Container: frontend_node_prod_2
resource "docker_container" "frontend_node_prod_2" {
  image = docker_image.app_image.image_id
  name  = "frontend_node_prod_2"
  
  ports {
    internal = 80
    external = 8082
  }
}

# Generated Container: backend_api_node_prod
resource "docker_container" "backend_api_node_prod" {
  image = docker_image.app_image.image_id
  name  = "backend_api_node_prod"
  
  ports {
    internal = 80
    external = 9001
  }
}
