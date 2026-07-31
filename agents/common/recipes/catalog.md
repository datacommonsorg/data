# Import-support recipe catalog

Recipes describe one read-only operational outcome. Skills should link to the
specific recipe needed instead of loading this catalog in full.

| Recipe ID | Outcome |
|---|---|
| `repository.resolve-import` | Resolve a unique import name and local code |
| `repository.list-imports` | Search bounded repository-configured imports |
| `repository.preview-infrastructure` | Review required cloud resources before access |
| `gcp.scheduler.describe-job` | Verify Scheduler and decode its Workflow target |
| `gcp.workflows.list-import-executions` | List bounded logical runs |
| `gcp.workflows.describe-execution` | Describe one exact logical run |
| `gcp.batch.describe-job` | Inspect one Batch job |
| `gcp.batch.list-tasks` | Inspect tasks for one Batch job |
| `gcp.logging.fetch-batch-logs` | Fetch bounded structured stage logs |
| `gcp.gcs.read-version-pointer` | Read one exact version pointer |
| `gcp.gcs.read-run-summary` | Read one exact run summary |
| `gcp.gcs.list-version-artifacts` | List files for one exact version |
| `gcp.gcs.find-historical-summary` | Find an older summary in a narrow date scope |
| `gcp.cloud-run.describe-ingestion-helper` | Resolve allowlisted helper coordinates |
| `gcp.spanner.read-import-records` | Read one current or historical record type |
| `gcp.cloud-build.resolve-runtime-provenance` | Correlate runtime image and source |
