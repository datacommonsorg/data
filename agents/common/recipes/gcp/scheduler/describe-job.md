# Describe and verify a Scheduler job

Recipe ID: `gcp.scheduler.describe-job`

## Use when

Checking whether an import is deployed for automatic refresh and identifying
its exact Workflow target.

## Required inputs

Simple import name, absolute import name, Scheduler project, and location.

## Clarify when

Project/location is missing or user, repository, and live scope conflict.

## Read-only operation

```bash
gcloud scheduler jobs describe <IMPORT_NAME> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --format=json | \
jq '{name, description, state, schedule, timeZone, attemptDeadline,
     retryConfig, lastAttemptTime, status,
     target_uri: .httpTarget.uri,
     target_import_name:
       (.httpTarget.body | @base64d | fromjson | .argument.importName)}'
```

## Preferred invocation

Run the command once. Verify both `description` and `target_import_name` equal
the resolved absolute import name. Do not retain the complete request body,
headers, or OAuth configuration.

## Expected output

Allowlisted schedule/delivery fields, exact Workflow target URI, and decoded
import identity.

## Required bounds

Describe exactly one named job. Never list every job or project.

## Evidence to retain

Resource name, description match, decoded import-name match, target URI, state,
schedule, and observation time.

## Common failures

Missing or paused job, permission denied, body decoding failure, name-only
match, or non-Workflow target.

## Related repository sources

`import-automation/executor/app/executor/cloud_scheduler.py` and
`import-automation/executor/app/executor/scheduler_job_manager.py`.
