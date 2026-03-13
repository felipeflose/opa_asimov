terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  credentials = file("../service-account.json")
  project     = var.project_id
  region      = var.region
}

variable "project_id" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The region to deploy resources in"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "The name of the GCS bucket"
  type        = string
  default     = "flose-ai-platform"
}

resource "google_storage_bucket" "platform_bucket" {
  name     = var.bucket_name
  location = var.region
  
  labels = {
    project     = "flose-ai-platform"
    component   = "ai-system"
    owner       = "flose"
    environment = "prod"
    cost_center = "ai-research"
  }

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# Sub-directories (represented as empty objects in GCS)
resource "google_storage_bucket_object" "directories" {
  for_each = toset([
    "knowledge/",
    "agents/",
    "vectors/",
    "embeddings/",
    "logs/",
    "documentation/",
    "iceberg/",
    "terraform/",
    "agents/memory/"
  ])
  
  name    = each.key
  content = " "
  bucket  = google_storage_bucket.platform_bucket.name
}
