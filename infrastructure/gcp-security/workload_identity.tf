# 1. Create the Google IAM Service Account for the Agent
resource "google_service_account" "ai_agent_gsa" {
  account_id   = "github-issue-agent-sa"
  display_name = "GitHub Issue Agent Service Account"
}

# 2. Grant the GSA permissions to use Vertex AI and Cloud Logging
resource "google_project_iam_member" "agent_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ai_agent_gsa.email}"
}

resource "google_project_iam_member" "agent_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ai_agent_gsa.email}"
}

# 3. The Magic: Bind the Kubernetes Service Account (KSA) to the Google Service Account (GSA)
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.ai_agent_gsa.name
  role               = "roles/iam.workloadIdentityUser"

  # This tells GCP: "Trust the 'ai-agent-ksa' inside the 'platform-agents' namespace of our GKE cluster"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[platform-agents/ai-agent-ksa]"
  ]
}