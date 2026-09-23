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
# - Necessary GCP APIs (including BigQuery and BigQuery Connection)
# - Secret Manager for the import-config secret
# - GCS Buckets for imports and mounting
# - BigQuery Dataset and Federated Cloud Spanner Connection
# - Optional Spanner Instance and Database (or external Spanner DB path)
# - Artifact Registry for hosting Docker images (Flex Template & Executor)
# - Pub/Sub Topic and Subscription for triggering imports
# - Cloud Run Services, Cloud Run Jobs, and Cloud Workflows
# - Unified Service Account with necessary IAM roles for Workflows, Cloud Run, and BigQuery

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
    archive = {
      source  = "hashicorp/archive"
    }
    http = {
      source  = "hashicorp/http"
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

variable "create_spanner_instance" {
  description = "Whether to provision a new Spanner instance and database in this project"
  type        = bool
  default     = true
}

variable "spanner_instance_id" {
  description = "Spanner Instance ID (used if create_spanner_instance is true)"
  type        = string
  default     = "datcom-import-instance"
}

variable "spanner_database_id" {
  description = "Spanner Database ID (used if create_spanner_instance is true)"
  type        = string
  default     = "dc-import-db"
}

variable "spanner_database_path" {
  description = "Full Spanner database path (e.g. projects/datcom-store/instances/dc-graph-staging/databases/dc_graph). If provided, overrides local spanner instance/db."
  type        = string
  default     = ""
}

variable "bq_dataset_id" {
  description = "BigQuery Dataset ID for aggregation"
  type        = string
  default     = "datacommons"
}

variable "bq_connection_id" {
  description = "BigQuery Spanner Connection ID"
  type        = string
  default     = "bq_spanner_conn"
}

variable "dc_api_key" {
  description = "Data Commons API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "artifact_registry_url" {
  description = "Artifact Registry URL for Cloud Run images"
  type        = string
  default     = "us-docker.pkg.dev/datcom-ci/gcr.io"
}

variable "image_version" {
  description = "Container image tag version for services and jobs"
  type        = string
  default     = "stable"
}

variable "dataflow_template_path" {
  description = "GCS path prefix for Dataflow templates"
  type        = string
  default     = "gs://datcom-templates/templates/flex/"
}

variable "spanner_ingestion_workflow_path" {
  description = "Optional local path to spanner-ingestion-workflow.yaml. If empty, fetched from datacommonsorg/import master."
  type        = string
  default     = ""
}

# --- Project & External Data ---

data "google_project" "project" {
  project_id = var.project_id
}

data "http" "spanner_ingestion_workflow" {
  url = "https://raw.githubusercontent.com/datacommonsorg/import/master/pipeline/workflow/spanner-ingestion-workflow.yaml"
}

# --- Locals ---

locals {
  spanner_database_path = var.spanner_database_path != "" ? var.spanner_database_path : (
    var.create_spanner_instance ? "projects/${var.project_id}/instances/${var.spanner_instance_id}/databases/${var.spanner_database_id}" : ""
  )

  services = [
    "artifactregistry.googleapis.com",
    "batch.googleapis.com",
    "bigquery.googleapis.com",
    "bigqueryconnection.googleapis.com",
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

# --- APIs ---

resource "google_project_service" "services" {
  for_each = toset(local.services)
  project  = var.project_id
  service  = each.key

  disable_on_destroy = false
}

# --- Secret Manager ---

resource "google_secret_manager_secret" "import_config" {
  count     = var.dc_api_key != "" ? 1 : 0
  secret_id = "import-config"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "import_config_v1" {
  count       = var.dc_api_key != "" ? 1 : 0
  secret      = google_secret_manager_secret.import_config[0].id
  secret_data = jsonencode({
    dc_api_key = var.dc_api_key
  })
}

resource "google_secret_manager_secret" "dc_api_key" {
  count     = var.dc_api_key != "" ? 1 : 0
  secret_id = "dc-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "dc_api_key_v1" {
  count       = var.dc_api_key != "" ? 1 : 0
  secret      = google_secret_manager_secret.dc_api_key[0].id
  secret_data = var.dc_api_key
}

# --- GCS Buckets ---

resource "google_storage_bucket" "import_bucket" {
  name                        = "${var.project_id}-imports"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [google_project_service.services]
}

resource "google_storage_bucket" "mount_bucket" {
  name                        = "${var.project_id}-mount"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [google_project_service.services]
}

# --- BigQuery Dataset & Spanner Connection ---

resource "google_bigquery_dataset" "aggregation_dataset" {
  dataset_id                  = var.bq_dataset_id
  friendly_name               = "Data Commons Aggregation Dataset"
  description                 = "Dataset used for Data Commons import aggregations"
  location                    = var.region
  project                     = var.project_id
  delete_contents_on_destroy  = false

  depends_on = [google_project_service.services]
}

resource "google_bigquery_connection" "spanner_connection" {
  connection_id = var.bq_connection_id
  location      = var.region
  project       = var.project_id
  friendly_name = "Cloud Spanner Connection"
  description   = "Federated connection from BigQuery to Cloud Spanner"

  cloud_spanner {
    database        = local.spanner_database_path
    use_parallelism = true
  }

  depends_on = [google_project_service.services]
}

# --- Cloud Run Services & Jobs ---

resource "google_cloud_run_v2_service" "ingestion_helper" {
  name     = "ingestion-helper-service"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.automation_sa.email
    timeout         = "3600s"
    containers {
      image = "${var.artifact_registry_url}/datacommons-ingestion-helper:${var.image_version}"
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "LOCATION"
        value = var.region
      }
      env {
        name  = "SPANNER_DATABASE_PATH"
        value = local.spanner_database_path
      }
      env {
        name  = "GCS_BUCKET_ID"
        value = google_storage_bucket.import_bucket.name
      }
      env {
        name  = "SPANNER_INGESTION_WORKFLOW_NAME"
        value = "spanner-ingestion-workflow"
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
      image = "${var.artifact_registry_url}/datacommons-import-helper:${var.image_version}"
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "LOCATION"
        value = var.region
      }
      env {
        name  = "PROJECT_NUMBER"
        value = data.google_project.project.number
      }
      env {
        name  = "GCS_BUCKET_ID"
        value = google_storage_bucket.import_bucket.name
      }
      env {
        name  = "SPANNER_DATABASE_PATH"
        value = local.spanner_database_path
      }
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_job" "import_validator" {
  name                = "import-validator-job"
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    template {
      timeout         = "7200s"
      service_account = google_service_account.automation_sa.email
      containers {
        image = "${var.artifact_registry_url}/dc-import-validator:${var.image_version}"
        resources {
          limits = {
            cpu    = "4"
            memory = "16Gi"
          }
        }
      }
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_job" "aggregation_helper" {
  name                = "aggregation-helper-job"
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    template {
      timeout         = "21600s"
      service_account = google_service_account.automation_sa.email
      containers {
        image = "${var.artifact_registry_url}/datacommons-aggregation-helper:${var.image_version}"
        resources {
          limits = {
            cpu    = "4"
            memory = "16Gi"
          }
        }
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "LOCATION"
          value = var.region
        }
        env {
          name  = "SPANNER_DATABASE_PATH"
          value = local.spanner_database_path
        }
        env {
          name  = "GCS_BUCKET_ID"
          value = google_storage_bucket.import_bucket.name
        }
        env {
          name  = "BQ_DATASET_ID"
          value = google_bigquery_dataset.aggregation_dataset.dataset_id
        }
        env {
          name  = "BQ_SPANNER_CONN_ID"
          value = google_bigquery_connection.spanner_connection.name
        }
        env {
          name  = "ENABLE_EMBEDDINGS"
          value = "true"
        }
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
    LOCATION                 = var.region
    GCS_BUCKET_ID            = google_storage_bucket.import_bucket.name
    GCS_MOUNT_BUCKET         = google_storage_bucket.mount_bucket.name
    PROJECT_NUMBER           = data.google_project.project.number
    IMPORT_HELPER_SERVICE    = google_cloud_run_v2_service.import_helper.name
    INGESTION_HELPER_SERVICE = google_cloud_run_v2_service.ingestion_helper.name
  }

  depends_on = [google_project_service.services]
}

resource "google_workflows_workflow" "spanner_ingestion_workflow" {
  name            = "spanner-ingestion-workflow"
  region          = var.region
  project         = var.project_id
  description     = "Orchestrates Spanner ingestion"
  service_account = google_service_account.automation_sa.id
  source_contents = var.spanner_ingestion_workflow_path != "" ? file(var.spanner_ingestion_workflow_path) : data.http.spanner_ingestion_workflow.response_body

  user_env_vars = {
    LOCATION                 = var.region
    PROJECT_ID               = var.project_id
    SPANNER_DATABASE_PATH    = local.spanner_database_path
    PROJECT_NUMBER           = data.google_project.project.number
    DATAFLOW_TEMPLATE_PATH   = "${var.dataflow_template_path}ingestion-${var.image_version}.json"
    INGESTION_HELPER_SERVICE = google_cloud_run_v2_service.ingestion_helper.name
    AGGREGATION_JOB_NAME     = google_cloud_run_v2_job.aggregation_helper.name
  }

  depends_on = [google_project_service.services]
}

# --- Spanner (Optional / Local Provisioning) ---

resource "google_spanner_instance" "import_instance" {
  count        = var.create_spanner_instance ? 1 : 0
  name         = var.spanner_instance_id
  config       = "regional-${var.region}"
  display_name = "Import Automation"
  num_nodes    = 1
  project      = var.project_id

  depends_on = [google_project_service.services]
}

resource "google_spanner_database" "import_db" {
  count               = var.create_spanner_instance ? 1 : 0
  instance            = google_spanner_instance.import_instance[0].name
  name                = var.spanner_database_id
  project             = var.project_id
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
    "roles/bigquery.admin",
    "roles/bigquery.connectionUser",
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
    push_endpoint = "${google_cloud_run_v2_service.import_helper.uri}/imports/feed"
    oidc_token {
      service_account_email = google_service_account.automation_sa.email
    }
  }
}

# --- Outputs ---

output "automation_service_account_email" {
  value       = google_service_account.automation_sa.email
  description = "The email of the service account used for import automation."
}

output "bq_dataset_id" {
  value       = google_bigquery_dataset.aggregation_dataset.dataset_id
  description = "BigQuery dataset ID for aggregations"
}

output "bq_spanner_connection_id" {
  value       = google_bigquery_connection.spanner_connection.name
  description = "BigQuery Spanner external connection name"
}

output "gcs_import_bucket" {
  value       = google_storage_bucket.import_bucket.name
  description = "GCS bucket name for import artifacts"
}

output "gcs_mount_bucket" {
  value       = google_storage_bucket.mount_bucket.name
  description = "GCS bucket name for mounting inside batch jobs"
}
