# Import Automation System

The import automation system has two components:
- Import Job (Cloud Batch)
- Ingestion Pipeline (Dataflow + Cloud Workflow)

## Import Job
Import jobs own the task of fetching data from external data sources and making it available for ingestion into the knowledge graph. Each import typically includes an import script along with a manifest file containing import metadata (e.g., refresh schedule). Adding a new data import to the stack involves adding the import script and manifest and then triggering the scheduler script which configures a Cloud Scheduler job for periodically running the import job. Detailed usage instructions on how to configure a new import job are available in the [user guide](executor/README.md).

The scheduler job triggers a GCP Workflow which then creates a GCP Batch job for each data import. An import job performs multiple tasks such as downloading data, processing it, and generating resolved mcf and copying it to GCS. It relies on the DataCommons [Import tool](https://github.com/datacommonsorg/import/blob/master/docs/usage.md) to perform mcf generation. Additionally, several validations are performed as part of the import job to ensure data quality. More details about the validation framework and supported validations can be found in the [README](https://github.com/datacommonsorg/data/tree/master/tools/import_validation).

Status of various import jobs can be monitored in the ImportStatus spanner table via the [Looker Studio dashboard](https://lookerstudio.google.com/c/reporting/e88fda74-50c9-46c6-88aa-c84342ceba48/).

## Ingestion Pipeline
DataCommons runs various import jobs on cloud batch that generate the output MCF data on GCS. The output from these jobs is consumed by the graph ingestion pipeline (Dataflow) to push data into the knowledge graph (Spanner). More details about the ingestion pipeline are available [here](https://github.com/datacommonsorg/import/tree/master/pipeline/ingestion). 

A GCP [cloud workflow](workflow/spanner-ingestion-workflow.yaml) is used to coordinate control between auto-refresh import jobs and the ingestion dataflow pipeline.  To maintain data consistency, a global lock is used to ensure that only a single execution of the workflow is active at any time. The workflow relies on various [Spanner tables](workflow/spanner_schema.sql) for metadata management and [helper cloud functions](workflow/ingestion-helper/README.md) to control the execution.

Infrastructure deployment for the various components in the import automation stack is automated using a [Terraform script](terraform/main.tf).

