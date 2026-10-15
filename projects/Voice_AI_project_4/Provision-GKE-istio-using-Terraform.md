---
title: "provision the underlying GKE cluster and configure these Istio components initially using Terraform"
parent: "6. Project 4 gcp voice AI"
nav_order: 4
---

# Project 4: provision the underlying GKE cluster and configure these Istio components initially using Terraform

To provision a production-grade GKE cluster and configure Istio for a UK financial institution, Terraform must enforce enterprise security, data residency, private connectivity, and compliance automation.

Implementation-level guide structured using modular, production-ready HashiCorp Terraform configuration code.

## 1. Network & VPC Foundation (network.tf)
Before launching GKE, set up a Private VPC with strict IP alias ranges for pods and services, along with Cloud NAT to block direct public internet access to node IPs.

```terraform
# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "voice-ai-vpc-prod"
  auto_create_subnetworks = false
}

# Subnet with Secondary IP Ranges for GKE Pods and Services
resource "google_compute_subnetwork" "gke_subnet" {
  name                     = "voice-ai-gke-subnet-uk"
  region                   = "europe-west2" # London region for UK compliance
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = "10.100.0.0/20"
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.200.0.0/16"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.201.0.0/20"
  }
}

# Cloud Router & NAT for Outbound Internet Access (Without Public IPs on Nodes)
resource "google_compute_router" "router" {
  name    = "voice-ai-router"
  region  = google_compute_subnetwork.gke_subnet.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "voice-ai-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
```

## 2. Hardened Private GKE Cluster (gke.tf)
This module provisions a Private GKE Cluster with Shielded Nodes, Workload Identity (to eliminate hardcoded GCP credentials in pods), and standard compute plus GPU node pools for low-latency Voice AI inference.

```terraform
# KMS Key for Cluster Encryption at Rest
resource "google_kms_crypto_key" "gke_key" {
  name     = "gke-etcd-encryption-key"
  key_ring = "projects/my-voice-ai-project/locations/europe-west2/keyRings/voice-ai-keyring"
}

# Private GKE Cluster
resource "google_container_cluster" "primary" {
  name                     = "voice-ai-cluster-prod"
  location                 = "europe-west2-a"
  remove_default_node_pool = true
  initial_node_count       = 1
  network                  = google_compute_network.vpc.id
  subnetwork               = google_compute_subnetwork.gke_subnet.id

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "my-voice-ai-project.svc.id.goog"
  }

  # Enable Private Cluster Configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false # Set true for internal management jump-boxes
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # IP Allocation for Alias IP
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  # Database Encryption using CMEK
  database_encryption {
    state    = "ENCRYPTED"
    key_name = google_kms_crypto_key.gke_key.id
  }

  # Release Channel
  release_channel {
    channel = "REGULAR"
  }
}

# Standard System Node Pool (DevOps Tools, Ingress Gateway, Dynatrace Agents)
resource "google_container_node_pool" "system_nodes" {
  name       = "system-node-pool"
  cluster    = google_container_cluster.primary.id
  location   = google_container_cluster.primary.location
  node_count = 3

  node_config {
    machine_type = "e2-standard-4"
    spot         = false

    # Service Account with minimal privileges
    service_account = google_service_account.gke_sa.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
}

# GPU Node Pool for Voice AI Inference Workloads
resource "google_container_node_pool" "ai_inference_nodes" {
  name       = "voice-ai-gpu-pool"
  cluster    = google_container_cluster.primary.id
  location   = google_container_cluster.primary.location
  node_count = 2

  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  node_config {
    machine_type = "g2-standard-8" # NVIDIA L4 GPU instance type
    
    guest_accelerator {
      type  = "nvidia-l4"
      count = 1
    }

    service_account = google_service_account.gke_sa.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]

    labels = {
      workload = "voice-ai-inference"
    }

    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }
}

# IAM Service Account for GKE Nodes
resource "google_service_account" "gke_sa" {
  account_id   = "gke-node-sa-prod"
  display_name = "Custom GKE Node Service Account"
}
```


## 3. Kubernetes & Helm Provider Setup (providers.tf)
To deploy Istio directly through Terraform, configure the helm and kubernetes providers using dynamic authentication credentials generated by the GKE cluster resource.

```terraform
data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.primary.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  }
}
```

## 4. Istio Service Mesh Deployment (istio.tf)
Using official Helm charts, provision istio-base, istiod (the control plane), and istio-ingress (the edge gateway proxy).

```terraform
# 1. Istio Namespace
resource "kubernetes_namespace" "istio_system" {
  metadata {
    name = "istio-system"
  }
}

# 2. Istio Base (CRDs)
resource "helm_release" "istio_base" {
  name       = "istio-base"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  version    = "1.20.0"
}

# 3. Istiod (Control Plane)
resource "helm_release" "istiod" {
  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  version    = "1.20.0"

  depends_on = [helm_release.istio_base]

  set {
    name  = "meshConfig.enableAutoMtls"
    value = "true"
  }

  set {
    name  = "meshConfig.defaultConfig.proxyMetadata.ISTIO_META_DNS_CAPTURE"
    value = "true"
  }
}

# 4. Istio Ingress Gateway
resource "helm_release" "istio_ingressgateway" {
  name       = "istio-ingressgateway"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  version    = "1.20.0"

  depends_on = [helm_release.istiod]

  set {
    name  = "service.type"
    value = "LoadBalancer"
  }

  # Ensure GCP creates Network Endpoint Groups (NEGs) for direct container-native load balancing
  set {
    name  = "service.annotations.cloud\\.google\\.com/neg"
    value = "{\"ingress\": true}"
  }
}
```

## 5. Istio Routing & Security Configuration (istio-manifests.tf)
Configure Strict mTLS, the Ingress Gateway, VirtualService, and DestinationRule resources for traffic routing and canary operations using kubectl_manifest or standard Kubernetes CRDs.

```terraform
# 1. Enforce Strict mTLS Across Entire Mesh
resource "kubernetes_manifest" "strict_mtls" {
  manifest = {
    apiVersion = "security.istio.io/v1beta1"
    kind       = "PeerAuthentication"
    metadata = {
      name      = "default"
      namespace = "istio-system"
    }
    spec = {
      mtls = {
        mode = "STRICT"
      }
    }
  }
  depends_on = [helm_release.istiod]
}

# 2. Istio Gateway Resource
resource "kubernetes_manifest" "voice_ai_gateway" {
  manifest = {
    apiVersion = "networking.istio.io/v1alpha3"
    kind       = "Gateway"
    metadata = {
      name      = "voice-ai-gateway"
      namespace = "istio-system"
    }
    spec = {
      selector = {
        istio = "ingressgateway"
      }
      servers = [
        {
          port = {
            number   = 443
            name     = "https"
            protocol = "HTTPS"
          }
          tls = {
            mode           = "SIMPLE"
            credentialName = "voice-ai-tls-cert" # Pre-created Kubernetes secret or ManagedCertificate
          }
          hosts = ["voice.finance-corp.co.uk"]
        }
      ]
    }
  }
  depends_on = [helm_release.istio_ingressgateway]
}

# 3. Istio DestinationRule (Defines Subsets v1 & v2 for Canary Rollouts)
resource "kubernetes_manifest" "voice_ai_destination_rule" {
  manifest = {
    apiVersion = "networking.istio.io/v1alpha3"
    kind       = "DestinationRule"
    metadata = {
      name      = "voice-ai-service-dr"
      namespace = "prod-voice-ai"
    }
    spec = {
      host = "voice-ai-service.prod-voice-ai.svc.cluster.local"
      trafficPolicy = {
        tls = {
          mode = "ISTIO_MUTUAL"
        }
        connectionPool = {
          tcp = { maxConnections = 1024 }
          http = { http1MaxPendingRequests = 100, maxRequestsPerConnection = 10 }
        }
      }
      subsets = [
        {
          name = "v1"
          labels = {
            version = "v1"
          }
        },
        {
          name = "v2"
          labels = {
            version = "v2"
          }
        }
      ]
    }
  }
}

# 4. Istio VirtualService (Initial State: 100% to v1 Baseline)
resource "kubernetes_manifest" "voice_ai_virtual_service" {
  manifest = {
    apiVersion = "networking.istio.io/v1alpha3"
    kind       = "VirtualService"
    metadata = {
      name      = "voice-ai-vs"
      namespace = "prod-voice-ai"
    }
    spec = {
      hosts    = ["voice.finance-corp.co.uk"]
      gateways = ["istio-system/voice-ai-gateway"]
      http = [
        {
          name = "voice-ai-routing"
          route = [
            {
              destination = {
                host   = "voice-ai-service.prod-voice-ai.svc.cluster.local"
                subset = "v1"
              }
              weight = 100
            },
            {
              destination = {
                host   = "voice-ai-service.prod-voice-ai.svc.cluster.local"
                subset = "v2"
              }
              weight = 0
            }
          ]
        }
      ]
    }
  }
  depends_on = [kubernetes_manifest.voice_ai_gateway]
}
```

## Key Talking Points
* **Why Container-Native Load Balancing (NEGs)?**

Annotating the Istio ingress gateway service with [cloud.google.com/neg](https://cloud.google.com/neg): '{"ingress": true}' instructs GCP's external load balancer to direct traffic straight into the container endpoints. This skips double-proxying via kube-proxy, reducing critical latency for real-time Voice AI connections.

* **Strict mTLS Enforcement:**

Applying PeerAuthentication in STRICT mode guarantees encrypted, mutually authenticated communication between all internal microservices. This satisfies stringent UK banking regulatory frameworks (e.g., PRA, FCA compliance).

* **Automated Handoff to Harness:**

Terraform manages base platform resources (GKE, Istio base, initial CRDs). During release pipelines, Harness modifies the existing VirtualService weights directly via Kubernetes APIs, performing automated canary deployments and rollbacks seamlessly.
