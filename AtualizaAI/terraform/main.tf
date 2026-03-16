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
        name  = "GEMINI_MODEL"
        value_source {
          secret_key_ref {
            secret  = "GEMINI_MODEL"
            version = "latest"
          }
        }
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
      env {
        name  = "TELEGRAM_CHAT_ID"
        value_source {
          secret_key_ref {
            secret  = "TELEGRAM_CHAT_ID"
            version = "latest"
          }
        }
      }
      env {
        name  = "TELEGRAM_BOT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = "TELEGRAM_BOT_TOKEN"
            version = "latest"
          }
        }
      }
      env {
        name  = "NAPKIN_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "NAPKIN_API_KEY"
            version = "latest"
          }
        }
      }
      env {
        name  = "MASTER_KEY"
        value_source {
          secret_key_ref {
            secret  = "MASTER_KEY"
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
resource "google_secret_manager_secret" "gemini_model" {
  secret_id = "GEMINI_MODEL"
  replication {
    auto {}
  }
}

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

resource "google_secret_manager_secret" "tg_chat_id" {
  secret_id = "TELEGRAM_CHAT_ID"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "napkin_key" {
  secret_id = "NAPKIN_API_KEY"
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

resource "google_project_iam_member" "bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_cloud_run_v2_service.flose_platform.template[0].service_account}"
}

resource "google_project_iam_member" "bq_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
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

# 7. BigQuery for Analytics (Ideia 8)
resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "flose_analytics"
  friendly_name               = "Flose Analytics"
  description                 = "Logs interativos para análise profunda"
  location                    = var.region
  delete_contents_on_destroy = true
}

resource "google_bigquery_table" "interactions" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "interactions"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "agent", "type": "STRING", "mode": "REQUIRED"},
  {"name": "task", "type": "STRING", "mode": "NULLABLE"},
  {"name": "result", "type": "STRING", "mode": "NULLABLE"},
  {"name": "cost_usd", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "metadata", "type": "STRING", "mode": "NULLABLE"}
]
EOF
}

# 6. Cloud Scheduler Jobs
resource "google_cloud_scheduler_job" "briefing" {
  name      = "flose-daily-briefing"
  schedule  = "0 8 * * *"
  time_zone = "America/Sao_Paulo"
  http_target {
    uri         = "${google_cloud_run_v2_service.flose_platform.uri}/daily_briefing"
    http_method = "POST"
  }
}

resource "google_cloud_scheduler_job" "alerts" {
  name      = "flose-weekly-alerts"
  schedule  = "0 9 * * 1" # Segunda às 9h
  time_zone = "America/Sao_Paulo"
  http_target {
    uri         = "${google_cloud_run_v2_service.flose_platform.uri}/weekly_alerts"
    http_method = "POST"
  }
}

resource "google_cloud_scheduler_job" "report" {
  name      = "flose-weekly-report"
  schedule  = "0 18 * * 5" # Sexta às 18h
  time_zone = "America/Sao_Paulo"
  http_target {
    uri         = "${google_cloud_run_v2_service.flose_platform.uri}/weekly_report"
    http_method = "POST"
  }
}
