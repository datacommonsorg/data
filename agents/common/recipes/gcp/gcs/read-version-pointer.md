# Read one import version pointer

Recipe ID: `gcp.gcs.read-version-pointer`

## Use when

The current staging attempt or accepted version must be identified.

## Required inputs

Verified GCS project, bucket, import prefix, and exact pointer filename.

## Clarify when

The bucket/prefix is inferred rather than tied to the selected deployment.

## Read-only operation

```bash
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<POINTER_FILENAME>' \
  --project=<PROJECT>
```

## Preferred invocation

Read `staging_version.txt` for the most recent attempt that wrote a summary.
Read the configured accepted pointer, normally `latest_version.txt`, only for a
publication question.

## Expected output

One version string from one exact object.

## Required bounds

Read one exact object. Never list the import prefix to discover pointer names.

## Evidence to retain

Exact object URI, pointer role, returned version, and observation time.

## Common failures

Failure before summary creation, missing accepted version, wrong bucket/prefix,
permission denied, or a stale pointer.

## Related repository sources

`import-automation/executor/app/configs.py` and
`import-automation/executor/app/executor/import_executor.py`.
