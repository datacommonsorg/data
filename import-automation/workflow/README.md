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
   - **Validation Job**: Runs `dc-import-validator` Cloud Run Job (`import-validator-job`).
   - **Version Update & Staging Ingestion**: Updates version via `import-helper-service`, triggers staging ingestion via Spanner Cloud Workflow, and polls until completion.
   - **Production Ingestion**: Triggers fire-and-forget production Spanner ingestion upon staging success.
   - **Workflow Summary**: Aggregates execution status across stages and reports errors.

5. **`import-automation-workflow.yaml` & `import_automation_e2e.py`**:
   Google Cloud Workflows definition (`import-automation-workflow`) and integration test runner for legacy Cloud Workflows orchestration.

## Continuous Deployment

Cloud Build automatically updates the catalog, deploys `import-automation-workflow.yaml` to Cloud Workflows, and syncs DAGs to Cloud Composer:
- Config: `import-automation/workflow/cloudbuild.yaml`
- Target: `gs://<dag_bucket>/dags/datacommons_airflow/`
