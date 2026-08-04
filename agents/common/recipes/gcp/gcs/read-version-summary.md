# Read one import version summary

Recipe ID: `gcp.gcs.read-version-summary`

## Use when

Candidate classification, Batch job ID, or summary statistics are needed for
an already selected finalized version.

## Required inputs

GCS project and bucket from the effective environment; exact import identity
and version; expected simple import name; and, when already known, the expected
Batch job ID.

## Clarify when

The import identity or version is ambiguous. Accept an exact version supplied
by the user or obtained from a pointer or bounded summary-list result. Keep the
read scoped to the selected import's GCS prefix.

## Read-only operation

```bash
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<VERSION>/import_summary.json' \
  --project=<PROJECT> | \
jq '{import_name,job_id,status,latest_version,graph_path,next_refresh,
     execution_time,data_volume,import_stats}'
```

## Preferred invocation

Read `import_summary.json` for one exact version and require `import_name` to
match the selected import before using any status or statistics. When a Batch
job ID is already known, also require `job_id` to match. Otherwise retain the
summary's `job_id` as a discovered identifier and follow only that exact ID.
When an exact version is supplied independently, construct its URI using the
[import evidence flow](../../../references/import-automation/import-evidence-flow.md);
do not run the summary-list helper first.

## Expected output

Allowlisted summary identity, status, version/path, timing, volume, and import
statistics.

## Required bounds

Read one exact summary. Do not list artifacts or other summaries.

## Evidence to retain

Exact summary URI, import/job identity match, status, and fields used in the
answer.

## Common failures

Attempt or Batch failure before summary creation, identity mismatch, invalid
JSON, missing object, or permission denied. A missing summary is not proof that
no attempt occurred.

## Related repository sources

The [import executor](../../../../../import-automation/executor/app/executor/import_executor.py)
defines `ImportStatusSummary` and `_update_latest_version()`.
