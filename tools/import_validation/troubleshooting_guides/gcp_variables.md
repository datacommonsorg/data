# GCP Project and Bucket Glossary

This file defines the Google Cloud Platform (GCP) projects and Cloud Storage (GCS) buckets used across the Data Commons import pipelines, along with descriptions of their purposes.

## Variables

### `PROD_PROJECT`
* **Value:** `datcom-204919`
* **Description:** The production Google Cloud project where raw data imports, version logs, and validation outputs are published.

### `AUTO_REFRESH_PROJECT`
* **Value:** `datcom-import-automation-prod`
* **Description:** The production Google Cloud project dedicated to hosting the automated data refresh cron schedules, Cloud Batch jobs, and pipeline execution logs.

### `BQ_PROJECT`
* **Value:** `datcom-store`
* **Description:** The project containing Data Commons BigQuery tables (e.g., Knowledge Graph datasets like `datcom-store.dc_kg_latest.NLStatVars`).

### `PROD_BUCKET`
* **Value:** `datcom-prod-imports`
* **Description:** The primary production GCS storage bucket containing import files, timestamped runs, differ outputs (`obs_diff_log.csv`), and validation results.

### `BASE_PROJECT`
* **Value:** `datcom`
* **Description:** The base container project referencing general storage and service operations.

### `LOOKER_DASHBOARD`
* **Value:** `https://lookerstudio.google.com/c/reporting/e88fda74-50c9-46c6-88aa-c84342ceba48/page/eaXdF`
* **Description:** The Looker Studio dashboard displaying the latest execution status of all auto refresh data pipelines.
