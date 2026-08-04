# List recent finalized import summaries

Recipe ID: `gcp.gcs.list-import-summaries`

## Use when

Up to five recent finalized versions and their Batch job IDs are needed for one
exact import.

## Required inputs

Exact absolute import name; GCS project and bucket from the effective
environment; optional explicit output prefix, empty by default; result limit
from 1 through 5.

## Clarify when

The import identity or GCS resource is unresolved. If more than 100 summary
names match, stop and report that the bounded history is unavailable.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/import_support/list_import_summaries.py \
  --absolute_import_name='<DIRECTORY>:<IMPORT_NAME>' \
  --gcs_project='<PROJECT>' \
  --gcs_bucket='<BUCKET>' \
  --gcs_output_prefix='<OPTIONAL_PREFIX>' \
  --limit='<1_TO_5>'
```

## Preferred invocation

Use the helper once. It lists only exact `*/import_summary.json` objects below
the import prefix, with a fixed 101-object sentinel. If at most 100 match, it
sorts timestamp-version names newest first and downloads no more than the
selected five summaries to validate `import_name` and extract `job_id`.

Use reverse lexicographic timestamp-version name ordering for this bounded
support path. This intentionally trusts folder names and can misorder versions
within the repeated Pacific hour at DST fall-back. The helper skips
non-timestamp override names and reports their count. If
`scan_truncated=true`, use no returned history and do not replace it with a
broader bucket, Workflow, or Batch search.

## Expected output

Top-level identity, requested and scan limits, scanned/returned counts,
truncation, skipped override count, and bounded issues. Each result contains
`version`, date derived from the version name, the exact `gcs_version_uri`
without a trailing slash, and `batch_job_id`. Append `/import_summary.json` to
the version URI only when the exact summary is needed.

## Required bounds

Scan at most 101 matching summary names to detect a 100-name overflow. Return at
most five timestamp-named versions and download at most those five summaries.

## Evidence to retain

Exact import prefix, project and bucket, requested limit, scan count,
truncation, skipped override count, selected versions, dates, exact GCS version
URIs, Batch job IDs, and issues.

## Common failures

Permission denied, missing credentials, more than 100 summaries, invalid JSON,
summary identity mismatch, missing Batch job ID, or only non-timestamp override
versions. A Batch failure before summary creation is intentionally absent: this
is finalized-version history, not complete attempt history.

## Related repository sources

[Artifact layout](../../../references/import-automation/artifact-layout.md),
[run and status model](../../../references/import-automation/run-and-status-model.md),
and `agents/common/import_support/list_import_summaries.py`.
