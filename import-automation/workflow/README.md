# Import Automation Workflow (Airflow / Cloud Composer)

This directory contains the Apache Airflow DAG definitions and dynamic factory for automating Data Commons data imports.

## Architecture

1. **`build_manifest_catalog.py`**:
   Scans all `manifest.json` files in the repository (excluding `scripts/entities`) and compiles them into `imports_catalog.json`.
   To run manually:
   ```bash
   python3 import-automation/workflow/build_manifest_catalog.py
   ```

2. **`imports_catalog.json`**:
   The compiled catalog of all import configurations, cron schedules, curator emails, and resource allocations.

3. **`import_dags_factory.py`**:
   Airflow dynamic DAG factory that reads `imports_catalog.json` and registers an independent DAG for each import specification.
   All DAGs are created paused by default (`is_paused_upon_creation=True`, `catchup=False`).

4. **`import_automation_workflow.py`**:
   Core Airflow DAG definition that defines `build_dag` and executes the 4-stage pipeline:
   - **Cloud Batch Job**: Runs `dc-import-executor` container.
   - **Staging Ingestion**: Updates staging version via `import-helper-service-staging`, triggers ingestion via Spanner Cloud Workflow, and polls until completion.
   - **Production Ingestion**: Triggers fire-and-forget production Spanner ingestion upon staging success.
   - **Workflow Summary**: Aggregates execution status across stages and reports errors.

## Continuous Deployment

Cloud Build automatically updates the catalog and syncs DAGs to Cloud Composer:
- Config: `import-automation/cloudbuild/cloudbuild.workflow.yaml`
- Target: `gs://<dag_bucket>/dags/datacommons_airflow/`
