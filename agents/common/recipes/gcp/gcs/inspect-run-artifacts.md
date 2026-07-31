# Inspect one import run's GCS artifacts

Recipe ID: `gcp.gcs.inspect-run-artifacts`

## Use when

Resolving version pointers, import summary, input/output files, generated MCF,
or validation/differ artifacts.

## Required inputs

Verified bucket, import base prefix, optional version, and object limit.

## Clarify when

Workflow, Batch configuration, observed GCS, and Spanner point to different
buckets or prefixes.

## Read-only operation

```bash
gcloud storage objects list 'gs://<BUCKET>/<IMPORT_PREFIX>/**' \
  --project=<PROJECT> --sort-by='~name' --limit=<LIMIT> --format=json
gcloud storage objects list \
  'gs://<BUCKET>/<IMPORT_PREFIX>/**/import_summary.json' \
  --project=<PROJECT> --sort-by='~name' --limit=51 --format=json
gcloud storage cat 'gs://<BUCKET>/<IMPORT_PREFIX>/<OBJECT>' \
  --project=<PROJECT>
```

## Preferred invocation

Use the snapshot collector. Discover up to 50 summaries independently of the
general artifact listing, then read only summaries whose import and job IDs
match the run evidence. List metadata for data artifacts rather than
downloading their contents.

## Expected output

Observed staging/accepted pointer values, version, import summary, categorized
object URIs, sizes, and update times.

## Required bounds

Use one verified import prefix, at most 50 summaries, and at most 1,000 general
objects per import snapshot. Report summary and object truncation separately.

## Evidence to retain

Exact URI, generation/update time, size, pointer value, summary status, and
summary job ID.

## Common failures

Attempt failed before upload, pointer/summary mismatch, expired/deleted object,
permission denied, or listing truncation.

## Related repository sources

`import_executor.py`, `file_uploader.py`, executor config fields, and
[Artifact layout](../../../references/import-automation/artifact-layout.md).
