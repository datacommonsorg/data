# Data Commons Import Helper Service

FastAPI Cloud Run service (`import-helper-service` / `import-helper-service-staging`) providing helper endpoints for the Data Commons Import Automation workflow:
- `POST /imports/status`: Updates import job status and metadata in Cloud Spanner (`ImportSummary`, `ImportHistory`) and GCS (`staging_version.txt`, `latest_version.txt`, `import_summary.json`, `import_metadata_mcf.mcf`).
- `POST /imports/version`: Promotes/overrides import versions in Cloud Spanner and GCS prior to Spanner ingestion.
- `POST /imports/feed`: Processes Pub/Sub push notifications for CDA transfer completion and invokes downstream Cloud Composer (Airflow) DAGs or Cloud Workflows.
- `POST /database/initialize`: Initializes `ImportSummary` and `ImportHistory` tables in Cloud Spanner.

## Running Unit Tests Locally

```bash
cd import-automation/helper
uv run pytest
```

## Continuous Integration & Deployment (Cloud Build)

To run the full CI/CD build, test, and deployment pipeline from the `data` repository root:

```bash
gcloud builds submit . \
  --config=import-automation/helper/cloudbuild.yaml \
  --project=datcom-ci
```

To build and push a custom-tagged image without deploying:

```bash
cd import-automation/helper
gcloud builds submit . \
  --config=cloudbuild.yaml \
  --project=datcom-ci \
  --substitutions=_VERSION=dev-<your-name>,_DEPLOY_SERVICES=false
```
