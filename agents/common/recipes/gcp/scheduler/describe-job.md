# Describe and verify a Scheduler job

Recipe ID: `gcp.scheduler.describe-job`

## Use when

Checking whether an import is deployed for automatic refresh and identifying
the exact Workflow target.

## Required inputs

Import name, absolute import name, Scheduler project, and Scheduler location.

## Clarify when

Project/location is missing or user, repository, and live scope conflict.

## Read-only operation

```bash
gcloud scheduler jobs describe <IMPORT_NAME> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --format=json
```

## Preferred invocation

Use the shared snapshot collector, which allowlists fields and decodes the
base64 HTTP body. Verify `description` and parsed
`httpTarget.body.argument.importName` against the absolute name.

## Expected output

State, schedule, timezone, retry/deadline fields, last delivery metadata, full
resource name, and exact Workflow target URI.

## Required bounds

Describe exactly one named job. Never list every project or location.

## Evidence to retain

Resource name, description match, decoded import-name match, target URI, and
observation time. Retain no token or complete body.

## Common failures

Missing/paused job, permission denied, body decoding failure, name-only match,
or non-Workflow target.

## Related repository sources

`cloud_scheduler.py`, `scheduler_job_manager.py`, and `cloud_batch.py`.
