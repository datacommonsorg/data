# Terraform deployment for Data Commons Import Automation Workflow
#
# Usage:
# - Authenticate and set up application default credentials for Terraform to access GCP using 'gcloud auth login --update-adc'.
# - Obtain DataCommons API key: Get an API key portal https://apikeys.datacommons.org/ to be used as the `dc_api_key` variable.
# - Deploy the infrastructure and resources defined in this configuration using 'terraform apply'.
# - The output service account needs to have required permissions to access external resources.
#
# Input variables:
# - GCP project id
# - DC API key
#
# This file sets up:
# - Necessary GCP APIs
# - Secret Manager for the import-config secret
# - GCS Buckets for imports, mounting, and Dataflow templates
# - Spanner Instance and Database
# - Artifact Registry for hosting Docker images (Flex Template & Executor)
# - Pub/Sub Topic and Subscription for triggering imports
# - Cloud Functions, Workflows, and Ingestion Pipeline
# - Unified Service Account with necessary IAM roles for Workflows, Functions, and Pub/Sub

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
    archive = {
      source  = "hashicorp/archive"
    }
  }
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

variable "spanner_instance_id" {
  description = "Spanner Instance ID"
  type        = string
  default     = "datcom-import-instance"
}

variable "spanner_database_id" {
  description = "Spanner Database ID"
  type        = string
  default     = "dc-import-db"
}

variable "spanner_graph_database_id" {
  description = "Spanner Graph Database ID"
  type        = string
  default     = "dc-import-db"
}

variable "bq_dataset_id" {
  description = "BigQuery Dataset ID for aggregation"
  type        = string
  default     = "datacommons"
}

variable "dc_api_key" {
  description = "Data Commons API Key"
  type        = string
  sensitive   = true
}

variable "artifact_registry_url" {
  description = "Artifact Registry URL for Cloud Run images"
  type        = string
  default     = "us-docker.pkg.dev/datcom-ci/gcr.io"
}

# --- APIs ---

locals {
  services = [
    "artifactregistry.googleapis.com",
    "batch.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "compute.googleapis.com",
    "dataflow.googleapis.com",
    "iam.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "spanner.googleapis.com",
    "storage.googleapis.com",
    "workflows.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  for_each = toset(local.services)
  project  = var.project_id
  service  = each.key

  disable_on_destroy = false
}

# --- Secret Manager ---

resource "google_secret_manager_secret" "import_config" {
  secret_id = "import-config"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "import_config_v1" {
  secret      = google_secret_manager_secret.import_config.id
  secret_data = jsonencode({
    dc_api_key = var.dc_api_key
  })
}

resource "google_secret_manager_secret" "dc_api_key" {
  secret_id = "dc-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "dc_api_key_v1" {
  secret      = google_secret_manager_secret.dc_api_key.id
  secret_data = var.dc_api_key
}

# --- GCS Buckets ---

resource "google_storage_bucket" "import_bucket" {
  name     = "${var.project_id}-imports"
  location = var.region
  project  = var.project_id
  uniform_bucket_level_access = true

  depends_on = [google_project_service.services]
}

resource "google_storage_bucket" "mount_bucket" {
  name     = "${var.project_id}-mount"
  location = var.region
  project  = var.project_id
  uniform_bucket_level_access = true

  depends_on = [google_project_service.services]
}

# --- Cloud Functions Source Packaging ---

# --- Cloud Functions ---

resource "google_cloud_run_v2_service" "ingestion_helper" {
  name     = "ingestion-helper-service"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.automation_sa.email
    containers {
      image = "${var.artifact_registry_url}/datacommons-ingestion-helper:latest"
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "SPANNER_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "SPANNER_INSTANCE_ID"
        value = var.spanner_instance_id
      }
      env {
        name  = "SPANNER_DATABASE_ID"
        value = var.spanner_database_id
      }
      env {
        name  = "SPANNER_GRAPH_DATABASE_ID"
        value = var.spanner_graph_database_id
      }
      env {
        name  = "GCS_BUCKET_ID"
        value = google_storage_bucket.import_bucket.name
      }
      env {
        name  = "LOCATION"
        value = var.region
      }
      env {
        name  = "BQ_DATASET_ID"
        value = var.bq_dataset_id
      }
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service" "import_helper" {
  name     = "import-helper-service"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.automation_sa.email
    containers {
      image = "${var.artifact_registry_url}/datacommons-import-helper:latest"
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "LOCATION"
        value = var.region
      }
      env {
        name  = "GCS_BUCKET_ID"
        value = google_storage_bucket.import_bucket.name
      }
      env {
        name  = "INGESTION_HELPER_URL"
        value = google_cloud_run_v2_service.ingestion_helper.uri
      }
    }
  }

  depends_on = [google_project_service.services]
}

# --- Cloud Workflows ---

resource "google_workflows_workflow" "import_automation_workflow" {
  name            = "import-automation-workflow"
  region          = var.region
  project         = var.project_id
  description     = "Orchestrates the import automation process"
  service_account = google_service_account.automation_sa.id
  source_contents = file("${path.module}/../workflow/import-automation-workflow.yaml")

  user_env_vars = {
    LOCATION             = var.region
    GCS_BUCKET_ID        = google_storage_bucket.import_bucket.name
    GCS_MOUNT_BUCKET     = google_storage_bucket.mount_bucket.name
    INGESTION_HELPER_URL = google_cloud_run_v2_service.ingestion_helper.uri
  }

  depends_on = [google_project_service.services]
}

resource "google_workflows_workflow" "spanner_ingestion_workflow" {
  name            = "spanner-ingestion-workflow"
  region          = var.region
  project         = var.project_id
  description     = "Orchestrates Spanner ingestion"
  service_account = google_service_account.automation_sa.id
  source_contents = file("${path.module}/../workflow/spanner-ingestion-workflow.yaml")

  user_env_vars = {
    LOCATION               = var.region
    PROJECT_ID             = var.project_id
    SPANNER_PROJECT_ID     = var.project_id
    SPANNER_INSTANCE_ID    = var.spanner_instance_id
    SPANNER_DATABASE_ID    = var.spanner_database_id
    INGESTION_HELPER_URL   = google_cloud_run_v2_service.ingestion_helper.uri
  }

  depends_on = [google_project_service.services]
}

# --- Spanner ---

resource "google_spanner_instance" "import_instance" {
  name         = var.spanner_instance_id
  config       = "regional-${var.region}"
  display_name = "Import Automation"
  num_nodes    = 1
  project      = var.project_id

  depends_on = [google_project_service.services]
}

resource "google_spanner_database" "import_db" {
  instance = google_spanner_instance.import_instance.name
  name     = var.spanner_database_id
  project  = var.project_id
  deletion_protection = false
}

# --- IAM ---

resource "google_service_account" "automation_sa" {
  account_id   = "import-automation-sa"
  display_name = "Service Account for Import Automation (Workflows & Functions)"
  project      = var.project_id
}

resource "google_project_iam_member" "automation_roles" {
  for_each = toset([
    "roles/workflows.admin",
    "roles/cloudfunctions.admin",
    "roles/run.admin",
    "roles/run.invoker",
    "roles/batch.jobsEditor",
    "roles/dataflow.admin",
    "roles/logging.logWriter",
    "roles/storage.objectAdmin",
    "roles/iam.serviceAccountUser",
    "roles/spanner.databaseAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/artifactregistry.admin",
    "roles/secretmanager.secretAccessor",
    "roles/cloudbuild.builds.builder",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.automation_sa.email}"
}

# --- Artifact Registry ---

resource "google_artifact_registry_repository" "automation_repo" {
  location      = var.region
  repository_id = "import-automation"
  description   = "Docker repository for import automation images"
  format        = "DOCKER"
  project       = var.project_id

  depends_on = [google_project_service.services]
}

# --- Pub/Sub ---

resource "google_pubsub_topic" "import_automation_trigger" {
  name    = "import-automation-trigger"
  project = var.project_id
}

resource "google_pubsub_subscription" "import_automation_sub" {
  name    = "import-automation-sub"
  topic   = google_pubsub_topic.import_automation_trigger.name
  project = var.project_id

  filter = "attributes.transfer_status=\"TRANSFER_COMPLETED\""

  push_config {
    push_endpoint = google_cloud_run_v2_service.import_helper.uri
    oidc_token {
      service_account_email = google_service_account.automation_sa.email
    }
  }
}

# Outputs
output "automation_service_account_email" {
  value       = google_service_account.automation_sa.email
  description = "The email of the service account used for import automation."
}


