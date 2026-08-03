# Correlate import history and versions

Recipe ID: `gcp.imports.correlate-import-runs`

## Use when

Returning bounded version history for one import or tracing one exact GCS
version to its recorded Batch and Workflow identifiers.

## Required inputs

Mode, exact absolute import name, verified Spanner project/instance/database,
verified GCS project/bucket, optional deployment-specific GCS output prefix,
and either a history limit or exact version.

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

Pass `--gcs_output_prefix=<PREFIX>` only when verified for the selected live
deployment.

## Preferred invocation

Use `import_history` when the import is the entry point and `import_version`
when one version is already known. The helper makes one bounded Spanner query
and reads only exact `<version>/import_summary.json` objects. It does not call
Workflow or Batch APIs. Use their focused recipes afterward if live resource
state is requested.

## Expected output

Normalized absolute/simple import identity, Spanner name candidates, GCS
prefix, bounded version-history events, classified ET or L Workflow execution
references, unique exact GCS summary projections, Batch job IDs when present,
source timestamps, missing fields, warnings, and truncation.

## Required bounds

`import_history` defaults to the newest event when `--limit` is omitted. Its
limit must be 1 through 20. `import_version` returns at most 20 matching events.
Never list the import prefix or query all imports. A UTC range applies only to
the selected import's history.

## Evidence to retain

Canonical Spanner database, exact summary URIs, stored and normalized import
and version forms, history update timestamps, Workflow reference source,
Batch ID source, missing evidence, warnings, limit, and truncation.

## Common failures

Invalid absolute name or version, incomplete or invalid UTC range, permission
denied, schema drift, missing history, missing or invalid summary, inconsistent
stored name/version forms, absent Batch ID, or absent Workflow reference.
Missing per-version evidence can be a valid partial result.

## Related repository sources

`agents/common/import_support/correlate_import_runs.py`, the artifact-layout and
run/status references, and the supplied sibling ingestion-helper schema and
storage implementation.
