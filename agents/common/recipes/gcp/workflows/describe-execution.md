# Describe one Workflow execution

Recipe ID: `gcp.workflows.describe-execution`

## Use when

Inspecting one already selected logical run in more detail.

## Required inputs

Exact execution ID, Workflow ID, project, and location.

## Clarify when

The execution was not selected from the verified Workflow resource.

## Read-only operation

```bash
gcloud workflows executions describe <EXECUTION_ID> \
  --workflow=<WORKFLOW> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --format=json | \
jq '{name, state, createTime, startTime, endTime, duration,
     workflowRevisionId,
     result: (try (.result | fromjson | {jobId, importName}) catch {}),
     error:
       {context: ((.error.context // "")[:4000]),
        payload: ((.error.payload // "")[:4000])},
     current_steps:
       [.status.currentSteps[]? | {step, routine}]}'
```

## Preferred invocation

Describe only an execution returned by the bounded Workflow listing helper.
The projection omits the complete Workflow argument, allowlists result fields,
and bounds error strings.

## Expected output

Exact run state, times, revision, result, bounded error, and current steps.

## Required bounds

Describe one exact execution. Do not list neighboring executions.

## Evidence to retain

Execution resource, state, timestamps, Workflow revision, Batch job ID from the
result, and error or current-step fields used in the answer.

## Common failures

Expired execution, wrong Workflow, permission denied, or missing result after a
failure before Batch creation.

## Related repository sources

The live historical Workflow revision and the import-automation architecture
reference.
