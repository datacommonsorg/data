# List recent finalized import summaries

## Use when

Up to five recent finalized versions and their Batch job IDs are needed for one
exact import.

## Required inputs

Exact absolute import name; GCS project and bucket from the effective
environment; result limit from 1 through 5.

## Clarify when

The import identity or GCS resource is unresolved.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/scripts/list_import_summaries.py \
  --absolute_import_name='<DIRECTORY>:<IMPORT_NAME>' \
  --gcs_project='<PROJECT>' \
  --gcs_bucket='<BUCKET>' \
  --limit='<1_TO_5>'
```

## Preferred invocation

Use the helper once. It orders timestamp-version names newest first, downloads
only the selected summaries to validate `import_name` and extract `job_id`, and
reports skipped non-timestamp names. If `scan_truncated=true`, use no returned
history and do not replace it with a broader bucket, Workflow, or Batch search.

Reverse lexicographic ordering intentionally trusts folder names and can
misorder versions within the repeated Pacific hour at DST fall-back.

## Expected output

Top-level identity, requested and scan limits, scanned/returned counts,
truncation, skipped override count, and bounded issues. Each result contains
`version`, date derived from the version name, the exact `gcs_version_uri`
without a trailing slash, and `batch_job_id`. Append `/import_summary.json` to
the version URI only when the exact summary is needed.

## Required bounds

Scan up to 100 matching summary object names plus one overflow sentinel (101
names maximum). Return at most five timestamp-named versions and download at
most those five summaries.

## Evidence to retain

Exact import prefix and GCS resource, requested bounds, truncation, returned
version fields, and issues.

## Common failures

Permission denied, missing credentials, scan-limit overflow, invalid JSON,
summary identity mismatch, missing Batch job ID, or only non-timestamp names.
A Batch failure before summary creation is intentionally absent: this is
finalized-version history, not complete attempt history.

## Related repository sources

[Artifact layout](../../../references/import-automation/artifact-layout.md),
[import evidence flow](../../../references/import-automation/import-evidence-flow.md),
and the [summary-list helper](../../../scripts/list_import_summaries.py).
