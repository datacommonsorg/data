# Read one import version pointer

Recipe ID: `gcp.gcs.read-version-pointer`

## Use when

The most recent finalized candidate or current accepted ET output must be
identified.

## Required inputs

GCS project and bucket from the effective environment, plus the exact import
identity and one pointer role: most recent finalized candidate or current
accepted ET output.

## Clarify when

A required project, bucket, import identity, or pointer role is missing, or the
import prefix cannot be constructed from the exact import identity.

## Read-only operation

```bash
# Most recent finalized candidate
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/staging_version.txt' \
  --project=<PROJECT>

# Current accepted ET output
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/latest_version.txt' \
  --project=<PROJECT>
```

## Preferred invocation

Run only the command for the requested role. Read `staging_version.txt` for the
most recent finalized candidate. Read `latest_version.txt` for the current
accepted ET output.

To calculate `is_current`, compare the selected version exactly with the value
in `latest_version.txt`. This does not prove loader completion or serving
availability.

## Expected output

One version string from one exact object, labeled with its pointer role.

## Required bounds

Read one exact object. Never list the import prefix to discover pointer names.

## Evidence to retain

Exact object URI including the pointer filename, pointer role, returned version,
and observation time.

## Common failures

Failure before summary creation, missing accepted version, wrong bucket/prefix,
permission denied, or a stale pointer.

## Related repository sources

[Import environment defaults](../../../config/import-environments.yaml) and
[artifact layout](../../../references/import-automation/artifact-layout.md).
