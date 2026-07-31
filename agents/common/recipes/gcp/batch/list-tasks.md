# List tasks for one Batch job

Recipe ID: `gcp.batch.list-tasks`

## Use when

Task-level state, exit status, or runtime start time is required for a selected
Batch job.

## Required inputs

Exact Batch job ID, project, location, and task limit.

## Clarify when

The job ID or required result limit is missing.

## Read-only operation

```bash
gcloud batch tasks list \
  --job=<JOB_ID> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --limit=<LIMIT> \
  --format=json | \
jq '[.[] |
     {name,
      status:
        {state: .status.state,
         events: [.status.statusEvents[]?
                  | {type, eventTime, taskState}]}}]'
```

## Preferred invocation

Run only after job-level evidence is insufficient or provenance needs the
earliest task `RUNNING` event.

## Expected output

Bounded task resources, states, and status events.

## Required bounds

Use one exact job and an explicit limit. Report result truncation.

## Evidence to retain

Task resource, state, status events used, result limit, and truncation.

## Common failures

Expired tasks, permission denied, wrong location, or more tasks than the
selected limit.

## Related repository sources

`import-automation/executor/app/executor/cloud_batch.py`.
