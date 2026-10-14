# Project 4: Voice AI Infrastructure on GCP (UK Financial Sector)

## 1. Overview & Requirements
* **Domain:** UK Financial Sector (Requires strict compliance, data residency, and high security).
* **Workload:** Voice AI (Requires low-latency inference, rapid scaling, and high availability).
* **Role:** DevOps Implementation & Automation.

## 2. Infrastructure as Code (Terraform & GCP)
* **Core Goal:** Automate all GCP resource provisioning with security and auditability.
* **State Management:** Remote backend using GCS with Customer-Managed Encryption Keys (CMEK).
* **Security:** Enforce least-privilege service accounts and implement static code analysis (e.g., tfsec, Checkov) in the pipeline to catch misconfigurations.

## 3. Container Orchestration & Networking (GKE & Istio)
* **Kubernetes (GKE):** 
  * Optimize for AI workloads using Node Auto-Provisioning (NAP) and GPU/accelerator node pools.
  * Implement image streaming to reduce cold-start latency for large Voice AI models.
* **Service Mesh (Istio):**
  * **Traffic Routing:** Manage end-to-end traffic flow from the GCP load balancer to Istio ingress gateways and down to specific pods.
  * **Security:** Enforce strict mutual TLS (mTLS) for all service-to-service communication to meet zero-trust financial requirements.

## 4. CI/CD Pipeline (Harness)
* **Continuous Integration:** Build container images, run security scans, and generate SBOMs (Software Bill of Materials) early in the pipeline.
* **Continuous Deployment:** Integrate explicit Terraform `plan`, `approval`, and `apply` stages.
* **Progressive Delivery:** Utilize Istio’s advanced routing within Harness to execute safe canary rollouts and blue-green deployments.

## 5. Observability & AI Monitoring (Dynatrace)
* **Monitoring:** Feed Istio telemetry (metrics, logs, traces) into Dynatrace for full-stack visibility.
* **Davis AI:** Leverage Dynatrace's deterministic AI for automated root-cause analysis of latency spikes or application errors.
* **Reference Material:** Prioritize official Dynatrace PDF documentation and structured reading guides for deep technical understanding.

## 6. Agentic AI & Remediation
* **Automation Workflows:** Utilize Python-based multi-agent supervisor systems (e.g., LangGraph) to act on observability alerts.
* **Auto-Remediation:** Design agents capable of identifying infrastructure drift, fixing hardcoded credentials or Terraform misconfigurations, and automatically generating pull requests for review.