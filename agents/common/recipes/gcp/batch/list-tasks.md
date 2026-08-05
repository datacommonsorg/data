# List tasks for one Batch job

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
  --limit=<LIMIT_PLUS_ONE> \
  --format=json | \
jq --argjson limit '<LIMIT>' '
  {truncated: (length > $limit),
   tasks:
     [.[0:$limit][] |
      {name,
       status:
         {state: .status.state,
          events: [.status.statusEvents[]?
                   | {type, eventTime, taskState,
                      exitCode: .taskExecution.exitCode}]}}]}'
```

## Preferred invocation

Run only when job-level evidence does not answer the task-level state or
runtime-start question.

## Expected output

Bounded task resources, states, status events, task-execution exit codes when
present, and explicit truncation.

## Required bounds

Use one exact job and an explicit limit. Request `LIMIT_PLUS_ONE`, return at
most `LIMIT` tasks, and report whether the extra task exists.

## Evidence to retain

Task resource, state, status events used, task-execution exit code when present,
result limit, and truncation.

## Common failures

Expired tasks, permission denied, wrong location, or more tasks than the
selected limit.

## Related repository sources

`import-automation/executor/app/executor/cloud_batch.py`.
