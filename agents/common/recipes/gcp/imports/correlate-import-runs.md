# Correlate import history and versions

Recipe ID: `gcp.imports.correlate-import-runs`

## Use when

Returning bounded version history for one import or tracing one exact GCS
version to its recorded Batch and Workflow identifiers.

## Required inputs

Mode, exact absolute import name, Spanner project/instance/database and GCS
project/bucket from the effective environment, optional configured GCS output
prefix, and either a history limit or exact version.

## Clarify when

The absolute import name is unresolved, Spanner or GCS coordinates conflict,
the GCS output prefix is unknown for a deployment that uses one, or the caller
requests an unbounded history.

## Read-only operation

For import history:

```bash
./agents/common/run_python.sh \
  agents/common/import_support/correlate_import_runs.py \
  --mode=import_history \
  --absolute_import_name=<DIRECTORY:IMPORT_NAME> \
  --spanner_project=<SPANNER_PROJECT> \
  --spanner_instance=<SPANNER_INSTANCE> \
  --spanner_database=<SPANNER_DATABASE> \
  --gcs_project=<GCS_PROJECT> \
  --gcs_bucket=<GCS_BUCKET> \
  --limit=<LIMIT>
```

Add both `--start_time=<RFC3339>` and `--end_time=<RFC3339>` for an optional
start-inclusive, end-exclusive UTC-normalized history window.

For one exact version:

```bash
./agents/common/run_python.sh \
  agents/common/import_support/correlate_import_runs.py \
  --mode=import_version \
  --absolute_import_name=<DIRECTORY:IMPORT_NAME> \
  --version=<VERSION> \
  --spanner_project=<SPANNER_PROJECT> \
  --spanner_instance=<SPANNER_INSTANCE> \
  --spanner_database=<SPANNER_DATABASE> \
  --gcs_project=<GCS_PROJECT> \
  --gcs_bucket=<GCS_BUCKET>
```

Pass `--gcs_output_prefix=<PREFIX>` only when present in the effective
environment.

## Preferred invocation

Use `import_history` when the import is the entry point and `import_version`
when one version is already known. The helper makes one bounded Spanner query
for an exact version. For history, it makes one bounded version-discovery query
and one bounded event query for the selected versions. It reads only exact
`<version>/import_summary.json` objects and does not call
Workflow or Batch APIs. Use their focused recipes afterward if live resource
state is requested.

## Expected output

Minimal output containing the absolute import name and one ET record per
selected version. Each record has the version, exact GCS base path, import
Workflow execution ID, Batch job ID, Workflow-history timestamp, GCS-summary
creation timestamp, and missing identifiers. The top-level result also reports
truncation and, only when needed, incomplete-history issues. Name and version
normalization and loader Workflow events remain internal.

Use returned fields for optional detail lookups only when requested:

- `workflow_execution_id` with the effective environment's import Workflow
  project, location, and name for the Workflow description recipe.
- `batch_job_id` with the effective environment's Batch project and location
  for Batch job, task, or log recipes.
- `gcs_base_path` with the effective environment's GCS client project for the
  summary or bounded artifact-listing recipes.

## Required bounds

`import_history` defaults to the newest run when `--limit` is omitted. Its limit
counts unique versions and must be 1 through 20. `import_version` returns one
exact version. Never list the import prefix or query all imports. A UTC range
applies only to the selected import's history.

The caller must state the effective limit and optional UTC range alongside the
result. Those invocation bounds are intentionally not duplicated in the
minimal JSON output.

## Evidence to retain

Absolute import name, version, exact GCS base path, ET Workflow execution ID,
Batch job ID, returned timestamps, missing evidence, caller-supplied bounds,
issues, and truncation.

## Common failures

Invalid absolute name or version, incomplete or invalid UTC range, permission
denied, schema drift, missing history, missing or invalid summary, ambiguous ET
Workflow history, absent Batch ID, or absent Workflow reference. Missing
per-version evidence can be a valid partial result.

## Related repository sources

`agents/common/import_support/correlate_import_runs.py`, the artifact-layout and
run/status references, and the supplied sibling ingestion-helper schema and
storage implementation.
