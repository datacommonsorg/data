# Read one import version pointer

Recipe ID: `gcp.gcs.read-version-pointer`

## Use when

The current staging attempt or accepted version must be identified.

## Required inputs

GCS project and bucket from the effective environment, plus the exact import
identity and repository-defined pointer role.

## Clarify when

A required project, bucket, import identity, or pointer role is missing, or the
import prefix cannot be constructed from the exact import identity.

## Read-only operation

```bash
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<POINTER_FILENAME>' \
  --project=<PROJECT>
```

## Preferred invocation

Read `staging_version.txt` for the most recent attempt that wrote a summary.
Read the configured accepted pointer, normally `latest_version.txt`, only for a
current accepted ET-output question.

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

The runtime environment file and artifact-layout reference.
