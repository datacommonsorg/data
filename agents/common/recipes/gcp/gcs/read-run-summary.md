# Read one import run summary

Recipe ID: `gcp.gcs.read-run-summary`

## Use when

Pipeline status or summary statistics are needed for an already selected
version.

## Required inputs

GCS project, bucket, import-prefix template, and summary filename from the
effective environment; exact version; expected simple import name; and expected
Batch job ID.

## Clarify when

The version was not obtained from a pointer or bounded historical match.

## Read-only operation

```bash
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<VERSION>/<SUMMARY_FILENAME>' \
  --project=<PROJECT> | \
jq '{import_name,job_id,status,latest_version,graph_path,next_refresh,
     execution_time,data_volume,import_stats}'
```

## Preferred invocation

Read the configured summary filename for one exact version and require both
`import_name` and `job_id` to match the selected run before using any status or
statistics.

## Expected output

Allowlisted summary identity, status, version/path, timing, volume, and import
statistics.

## Required bounds

Read one exact summary. Do not list artifacts or other summaries.

## Evidence to retain

Exact summary URI, import/job identity match, status, and fields used in the
answer.

## Common failures

Attempt failed before summary creation, pointer changed after the selected run,
identity mismatch, invalid JSON, missing object, or permission denied.

## Related repository sources

`ImportStatusSummary` and `_update_latest_version()` in
`import-automation/executor/app/executor/import_executor.py`.
