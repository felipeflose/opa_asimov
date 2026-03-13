terraform {
  required_version = ">= 1.0"
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

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region"
  type        = string
  default     = "us-central1"
}

# 1. Cloud Run Service for the Dashboard
resource "google_cloud_run_v2_service" "flose_platform" {
  name     = "flose-ai-platform"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.project_id}/flose-ai-platform:latest"
      
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GEMINI_API_KEY"
        value = "TO_BE_SET" # Injest via Secret Manager for better security
      }
    }
  }
}

# 2. Artifact Registry for Docker Images
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "flose-repo"
  description   = "Docker repository for Flose AI Platform"
  format        = "DOCKER"
}

# 3. IAM - Allow public access to the dashboard (optional, or restrict to your IP)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.flose_platform.location
  name     = google_cloud_run_v2_service.flose_platform.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.flose_platform.uri
}
