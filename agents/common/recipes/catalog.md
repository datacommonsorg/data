# Import-support recipe catalog

Recipes describe one read-only operational outcome. Skills should link to the
specific recipe they need rather than load this catalog in full.

| Recipe ID | Outcome |
|---|---|
| `repository.resolve-import` | Resolve a unique import name and local code |
| `repository.list-imports` | Search bounded repository-configured imports |
| `repository.preview-infrastructure` | Print local cloud candidates before access |
| `gcp.scheduler.describe-job` | Verify Scheduler and decode its Workflow target |
| `gcp.workflows.list-import-executions` | List exact bounded logical runs |
| `gcp.batch.describe-job-and-tasks` | Inspect compute and task status |
| `gcp.logging.fetch-batch-logs` | Fetch bounded structured stage logs |
| `gcp.gcs.inspect-run-artifacts` | Resolve pointers, summary, and actual objects |
| `gcp.cloud-run.describe-ingestion-helper` | Resolve allowlisted helper coordinates |
| `gcp.spanner.read-import-records` | Read current, version, and ingestion records |
| `gcp.cloud-build.resolve-runtime-provenance` | Correlate runtime image and source |
