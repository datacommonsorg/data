# Describe a Batch job and tasks

Recipe ID: `gcp.batch.describe-job-and-tasks`

## Use when

A Workflow execution created or may have created Batch compute.

## Required inputs

Batch project, location, job ID, and expected absolute import name.

## Clarify when

More than one time-correlated candidate remains after runnable identity checks.

## Read-only operation

```bash
gcloud batch jobs describe <JOB_ID> \
  --project=<PROJECT> --location=<LOCATION> --format=json
gcloud batch tasks list \
  --job=<JOB_ID> --project=<PROJECT> --location=<LOCATION> --format=json
```

## Preferred invocation

Use the snapshot collector so command/environment output is allowlisted and the
full runnable import identity is verified.

## Expected output

Job/task state, allowlisted status-event fields, UID, resources, image URI,
timestamps, and verified import identity. The earliest task `RUNNING` event is
the preferred runtime-provenance bound.

## Required bounds

Describe one exact job and its bounded task set. Candidate listing must use a
time range and derived prefix.

## Evidence to retain

Full job name, UID, matched import field, state/status events, task result,
resources, and image URI.

## Common failures

Expired job, permission denied, lossy prefix collision, missing task, or
Workflow failure before Batch creation. Preserve Workflow `result.jobId` when
the Batch resource has expired.

## Related repository sources

`cloud_batch.py` and the live Workflow revision.
