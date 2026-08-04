# List artifacts for one import version

Recipe ID: `gcp.gcs.list-version-artifacts`

## Use when

Artifact metadata for input, output, MCF, validation, or differ files is needed
for one selected run.

## Required inputs

GCS project and bucket from the effective environment, exact import identity,
exact version, and result limit.

## Clarify when

The version is unknown or the requested artifact category is ambiguous.

## Read-only operation

```bash
gcloud storage objects list \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<VERSION>/**' \
  --project=<PROJECT> \
  --limit=<LIMIT_PLUS_ONE> \
  --format='json(name,bucket,size,updateTime,generation)'
```

## Preferred invocation

List metadata under one selected version. Filter returned names to the requested
artifact category; do not download data or MCF contents by default.

## Expected output

Bounded object URIs, sizes, update times, generations, and truncation.

## Required bounds

Use one exact version and an explicit result limit. Request one extra object to
detect truncation.

## Evidence to retain

Exact version URI, requested category, object metadata used, limit, and
truncation.

## Common failures

Wrong version, deleted objects, permission denied, or more objects than the
selected limit.

## Related repository sources

The [import executor](../../../../../import-automation/executor/app/executor/import_executor.py)
and [artifact layout](../../../references/import-automation/artifact-layout.md).
