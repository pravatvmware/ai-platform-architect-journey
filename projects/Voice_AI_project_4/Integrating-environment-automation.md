---
title: "Integrating Harness, Terraform, Google Kubernetes Engine (GKE), and Google Artifact Registry"
parent: "6. Project 4 gcp voice AI"
nav_order: 5
---

# Project 4: Integrating Harness, Terraform, Google Kubernetes Engine (GKE), and Google Artifact Registry

Integrating Harness, Terraform, Google Kubernetes Engine (GKE), and Google Artifact Registry (GAR—the modern replacement for Container Registry) requires a secure, automated bridge. In a financial services environment, this bridge must not expose your internal networks to the public internet.

The core of this integration is the Harness Delegate.

how these components securely interact?

## 1. The Architecture: The Harness Delegate
Harness operates on a SaaS model for its control plane (the UI and orchestration logic), but the execution happens securely within your GCP environment via the Harness Delegate.

You install the Delegate as a pod inside a management GKE cluster or on a Compute Engine VM.

The Delegate makes an outbound, polling connection (HTTPS/443) to the Harness SaaS. It asks, "Are there any pipeline tasks for me?"

When you trigger a pipeline, the SaaS tells the Delegate what to do.

Because the Delegate is running inside your GCP Virtual Private Cloud (VPC), it securely executes Terraform commands, authenticates to Artifact Registry, and deploys to your private GKE clusters using internal IP addresses.

## 2. Terraform Configuration: IAM & Artifact Registry
To make this work securely without passing static JSON service account keys around, you must configure GCP IAM, Workload Identity, and Artifact Registry.

``` terraform
# 1. Google Artifact Registry for Voice AI Images
resource "google_artifact_registry_repository" "voice_ai_repo" {
  location      = "europe-west2" # UK region
  repository_id = "voice-ai-images"
  description   = "Docker repository for Voice AI microservices"
  format        = "DOCKER"
  
  # CMEK encryption for financial compliance
  kms_key_name  = google_kms_crypto_key.gke_key.id 
}

# 2. IAM Service Account for the Harness Delegate
resource "google_service_account" "harness_delegate_sa" {
  account_id   = "harness-delegate-sa"
  display_name = "Harness Delegate Service Account"
}

# 3. Granting Necessary Permissions to the Delegate
# Permission to manage infrastructure via Terraform
resource "google_project_iam_member" "harness_tf_admin" {
  project = var.project_id
  role    = "roles/editor" # In production, restrict this to specific roles like Compute Admin, Network Admin, etc.
  member  = "serviceAccount:${google_service_account.harness_delegate_sa.email}"
}

# Permission to deploy to GKE
resource "google_project_iam_member" "harness_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.harness_delegate_sa.email}"
}

# Permission to pull images from Artifact Registry
resource "google_artifact_registry_repository_iam_member" "harness_gar_reader" {
  project    = google_artifact_registry_repository.voice_ai_repo.project
  location   = google_artifact_registry_repository.voice_ai_repo.location
  repository = google_artifact_registry_repository.voice_ai_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.harness_delegate_sa.email}"
}

# 4. Workload Identity Binding
# This allows the Harness Delegate pod in GKE to act as the GCP Service Account automatically
resource "google_service_account_iam_member" "harness_workload_identity" {
  service_account_id = google_service_account.harness_delegate_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[harness-delegate-namespace/harness-delegate-ksa]"
}
```

## 3. The Integration Flow
Once the infrastructure above is provisioned, the integration flows through these steps during a deployment:

* **1. Code Commit:** A developer merges code to the main branch.

* **2. CI Phase:** A CI tool (like GitHub Actions, GitLab CI, or Harness CI) builds the Docker image and pushes it to europe-west2-docker.pkg.dev/my-project/voice-ai-images/voice-ai:v2.0.

* **3. Trigger:** Harness detects the new image tag in GAR (or receives a webhook).

* **4. Terraform Execution (Optional Step):** Harness tells the Delegate to run a Terraform Plan/Apply to ensure the infrastructure (like the GKE node pools or Istio configurations) is in the correct state. The Delegate uses its Workload Identity to authenticate to GCP seamlessly.

* **5. Deployment:**

* Harness instructs the Delegate to deploy the updated Kubernetes and Istio manifests to the target GKE cluster.

* Harness dynamically injects the new Artifact Registry image URL (voice-ai:v2.0) into the Kubernetes Deployment manifest.

* **6. Image Pull:** The GKE worker nodes authenticate to Artifact Registry (using their own Node Service Account) and pull the new container image to start the pods.

## 4. Harness Pipeline YAML Snippet
Within Harness, this integration is represented as a pipeline. Here is a conceptual YAML snippet showing how Harness connects these tools:

```terraform
pipeline:
  name: Voice AI Production Deployment
  stages:
    - stage:
        name: Infrastructure Provisioning
        type: Custom
        spec:
          execution:
            steps:
              - step:
                  type: TerraformApply
                  name: Apply Infrastructure Changes
                  spec:
                    provisionerIdentifier: gcp_terraform
                    delegateSelectors:
                      - primary-gcp-delegate # Targets your specific delegate
                    workspace: prod
                    
    - stage:
        name: Deploy Canary
        type: Deployment
        spec:
          infrastructure:
            environmentRef: prod-env
            infrastructureDefinition:
              type: KubernetesDirect
              spec:
                connectorRef: gcp-gke-connector # Authenticated via Delegate Workload Identity
                namespace: prod-voice-ai
          execution:
            steps:
              - step:
                  type: K8sCanaryDeploy
                  name: Canary Deployment
                  spec:
                    skipDryRun: false
                    # Harness automatically pulls manifests from Git and targets the new image in GAR
```

* This setup ensures that Harness orchestrates the release, Terraform manages the state, and GCP hosts the secure, private execution environment.
