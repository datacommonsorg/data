# Describe and verify a Scheduler job

## Use when

Checking whether an import is deployed for automatic refresh and identifying
its exact Workflow target.

## Required inputs

Simple import name, absolute import name, Scheduler project/location, and the
configured Workflow resource from the effective environment.

## Clarify when

A required input is missing or explicit prompt values conflict.

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
       (if .httpTarget.body
        then (.httpTarget.body | @base64d | fromjson | .argument.importName)
        else null
        end)}'
```

## Preferred invocation

Run the command once. Verify both `description` and `target_import_name` equal
the resolved absolute import name and `target_uri` identifies the configured
Workflow. Report infrastructure drift and stop if it points outside the
effective scope. Do not retain the complete request body, headers, or OAuth
configuration.

## Expected output

Allowlisted schedule/delivery fields, exact Workflow target URI, and decoded
import identity. A missing HTTP body produces `target_import_name: null`; treat
that as target drift, not successful verification.

## Required bounds

Describe exactly one named job. Never list every job or project.

## Evidence to retain

Resource name, description match, decoded import-name match, target URI, state,
schedule, and observation time.

## Common failures

Missing or paused job, permission denied, missing body, body decoding failure,
name-only match, non-Workflow target, or target/configuration drift. Invalid
Base64 or JSON remains a decoding failure rather than being converted to null.

## Related repository sources

`import-automation/executor/app/executor/cloud_scheduler.py` and
`import-automation/executor/app/executor/scheduler_job_manager.py`.
