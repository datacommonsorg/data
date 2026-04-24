# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
# - Spanner Instance and Database with schema
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

variable "github_owner" {
  description = "The owner of the GitHub repository"
  type        = string
  default     = "datacommonsorg"
}

variable "github_repo_name" {
  description = "The name of the GitHub repository (data)"
  type        = string
  default     = "data"
}

variable "github_repo_ingestion_name" {
  description = "The name of the GitHub repository (import)"
  type        = string
  default     = "import"
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

# New Variables
variable "ingestion_helper_image" {
  description = "The Docker image for the ingestion helper service"
  type        = string
  default     = "us-docker.pkg.dev/datcom-ci/gcr.io/datacommons-ingestion-helper:latest"
}

variable "spanner_project_id" {
  description = "Spanner Project ID"
  type        = string
  default     = ""
}

variable "gcs_bucket_id" {
  description = "GCS Bucket ID for imports (overrides default generated bucket)"
  type        = string
  default     = ""
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
  spanner_project_id = var.spanner_project_id != "" ? var.spanner_project_id : var.project_id
  gcs_bucket_id      = var.gcs_bucket_id != "" ? var.gcs_bucket_id : google_storage_bucket.import_bucket.name
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

data "archive_file" "aggregation_helper_source" {
  type        = "zip"
  source_dir  = "${path.module}/../workflow/aggregation-helper"
  output_path = "${path.module}/aggregation_helper.zip"
}

data "archive_file" "import_helper_source" {
  type        = "zip"
  source_dir  = "${path.module}/../workflow/import-helper"
  output_path = "${path.module}/import_helper.zip"
}

resource "google_storage_bucket_object" "aggregation_helper_zip" {
  name   = "function-source/aggregation_helper.${data.archive_file.aggregation_helper_source.output_md5}.zip"
  bucket = google_storage_bucket.import_bucket.name
  source = data.archive_file.aggregation_helper_source.output_path
}

resource "google_storage_bucket_object" "import_helper_zip" {
  name   = "function-source/import_helper.${data.archive_file.import_helper_source.output_md5}.zip"
  bucket = google_storage_bucket.import_bucket.name
  source = data.archive_file.import_helper_source.output_path
}

# --- Cloud Functions ---

resource "google_cloudfunctions2_function" "aggregation_helper" {
  name        = "import-aggregation-helper"
  location    = var.region
  project     = var.project_id
  description = "Helper for import aggregation"

  build_config {
    runtime     = "python312"
    entry_point = "aggregation_helper"
    source {
      storage_source {
        bucket = google_storage_bucket.import_bucket.name
        object = google_storage_bucket_object.aggregation_helper_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "256M"
    timeout_seconds    = 60
    service_account_email = google_service_account.automation_sa.email
    environment_variables = {
      PROJECT_ID          = var.project_id
      SPANNER_PROJECT_ID  = local.spanner_project_id
      SPANNER_INSTANCE_ID = var.spanner_instance_id
      SPANNER_DATABASE_ID = var.spanner_database_id
      GCS_BUCKET_ID       = local.gcs_bucket_id
      LOCATION            = var.region
      BQ_DATASET_ID       = var.bq_dataset_id
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloudfunctions2_function" "import_helper" {
  name        = "import-automation-helper"
  location    = var.region
  project     = var.project_id
  description = "Helper for import automation"

  build_config {
    runtime     = "python312"
    entry_point = "handle_feed_event"
    source {
      storage_source {
        bucket = google_storage_bucket.import_bucket.name
        object = google_storage_bucket_object.import_helper_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "256M"
    timeout_seconds    = 60
    service_account_email = google_service_account.automation_sa.email
    environment_variables = {
      PROJECT_ID    = var.project_id
      LOCATION      = var.region
      GCS_BUCKET_ID = local.gcs_bucket_id
    }
  }

  depends_on = [google_project_service.services]
}

# --- Cloud Run Service ---

resource "google_cloud_run_v2_service" "ingestion_helper_service" {
  name     = "ingestion-helper-service"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = var.ingestion_helper_image
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "SPANNER_PROJECT_ID"
        value = local.spanner_project_id
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
        name  = "GCS_BUCKET_ID"
        value = local.gcs_bucket_id
      }
      env {
        name  = "LOCATION"
        value = var.region
      }
    }
    # Using the default compute SA to avoid permission issues
    service_account = "965988403328-compute@developer.gserviceaccount.com"
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
    LOCATION          = var.region
    GCS_BUCKET_ID     = google_storage_bucket.import_bucket.name
    GCS_MOUNT_BUCKET  = google_storage_bucket.mount_bucket.name
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
    LOCATION            = var.region
    PROJECT_ID          = var.project_id
    SPANNER_PROJECT_ID  = local.spanner_project_id
    SPANNER_INSTANCE_ID = var.spanner_instance_id
    SPANNER_DATABASE_ID = var.spanner_database_id
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
  ddl      = [for s in split(";", file("${path.module}/../workflow/spanner_schema.sql")) : trimspace(s) if trimspace(s) != ""]

  deletion_protection = false
}

# Initialize IngestionLock (DML)
resource "null_resource" "init_spanner_lock" {
  provisioner "local-exec" {
    command = <<EOT
gcloud spanner databases execute-sql ${google_spanner_database.import_db.name} \
  --instance=${google_spanner_instance.import_instance.name} \
  --project=${var.project_id} \
  --sql="INSERT INTO IngestionLock (LockID) VALUES ('global_ingestion_lock')" || echo 'Lock already exists'
EOT
  }

  depends_on = [google_spanner_database.import_db]
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
    push_endpoint = google_cloudfunctions2_function.import_helper.service_config[0].uri
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
