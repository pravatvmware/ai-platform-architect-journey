variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "project_number" {
  type        = string
  description = "GCP Project Number"
}

variable "organization_id" {
  type        = string
  description = "GCP Organization ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
}

variable "trusted_ip_ranges" {
  type        = list(string)
  description = "Trusted corporate IP ranges allowed to bypass perimeter restrictions"
  default     = ["10.0.0.0/8"]
}