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
        value_source {
          secret_key_ref {
            secret  = "GEMINI_API_KEY"
            version = "latest"
          }
        }
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

# 3. Secret Manager (Managed for stability)
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "GEMINI_API_KEY"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "tg_token" {
  secret_id = "TELEGRAM_BOT_TOKEN"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "master_key" {
  secret_id = "MASTER_KEY"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "admin_email" {
  secret_id = "ADMIN_EMAIL"
  replication {
    auto {}
  }
}

# 4. IAM - Permissions for the service account
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_cloud_run_v2_service.flose_platform.template[0].service_account}"
}

# 5. IAM - Allow public access to the dashboard (optional, or restrict to your IP)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.flose_platform.location
  name     = google_cloud_run_v2_service.flose_platform.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.flose_platform.uri
}
