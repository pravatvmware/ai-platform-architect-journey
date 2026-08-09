terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Access Context Manager Policy
resource "google_access_context_manager_access_policy" "ai_policy" {
  parent = "organizations/${var.organization_id}"
  title  = "Enterprise AI Security Policy"
}

# 2. Access Level (Defines trusted sources, e.g., Corporate CIDR / IP range)
resource "google_access_context_manager_access_level" "corporate_network" {
  parent = "accessPolicies/${google_access_context_manager_access_policy.ai_policy.name}"
  name   = "accessPolicies/${google_access_context_manager_access_policy.ai_policy.name}/accessLevels/corporate_network_level"
  title  = "Corporate Network Level"
  
  basic {
    conditions {
      ip_subnetworks = var.trusted_ip_ranges
    }
  }
}

# 3. VPC Service Control Service Perimeter
resource "google_access_context_manager_service_perimeter" "ai_data_perimeter" {
  parent         = "accessPolicies/${google_access_context_manager_access_policy.ai_policy.name}"
  name           = "accessPolicies/${google_access_context_manager_access_policy.ai_policy.name}/servicePerimeters/ai_data_perimeter"
  title          = "Enterprise AI Data Protection Perimeter"
  perimeter_type = "PERIMETER_TYPE_REGULAR"

  status {
    # Restricted GCP Services inside the perimeter
    restricted_services = [
      "aiplatform.googleapis.com",       # Vertex AI APIs
      "sqladmin.googleapis.com",         # Cloud SQL / AlloyDB
      "storage.googleapis.com"          # Enterprise Data Buckets
    ]

    access_levels = [
      google_access_context_manager_access_level.corporate_network.name
    ]

    resources = [
      "projects/${var.project_number}"
    ]
  }
}