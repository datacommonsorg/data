# Inspect Workflow executions

Recipe ID: `gcp.workflows.list-import-executions`

## Use when

Listing refresh runs for one import or across multiple imports in a bounded time
window, or describing one exact execution ID supplied by the caller.

## Required inputs

For listing: full Workflow resource, UTC start/end, result limit, scan limit,
and optional exact absolute import name. For exact description: execution ID,
Workflow ID, project, and location.

## Clarify when

The effective environment and prompt overrides do not resolve to exactly one
full Workflow resource.

## Read-only operation

For one import:

```bash
./agents/common/run_python.sh \
  agents/common/import_support/list_import_runs.py \
  --workflow_resource=<FULL_RESOURCE> \
  --absolute_import_name=<DIRECTORY:IMPORT_NAME> \
  --start_time=<RFC3339_UTC> \
  --end_time=<RFC3339_UTC> \
  --run_limit=<LIMIT> \
  --scan_limit=<SCAN_LIMIT>
```

For a query across multiple imports, omit `--absolute_import_name`.

For one caller-supplied exact execution ID:

```bash
gcloud workflows executions describe <EXECUTION_ID> \
  --workflow=<WORKFLOW> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --format=json | \
jq '{name, state, createTime, startTime, endTime, duration,
     workflowRevisionId,
     argument: (try (.argument | fromjson | {importName}) catch {}),
     result: (try (.result | fromjson | {jobId, importName}) catch {}),
     error:
       {context: ((.error.context // "")[:4000]),
        payload: ((.error.payload // "")[:4000])},
     current_steps:
       [.status.currentSteps[]? | {step, routine}]}'
```

## Preferred invocation

For “last run,” search the previous 90 days and return one matching execution.

Use this focused helper because the installed `gcloud workflows executions
list` command cannot request FULL view and therefore omits `argument.importName`.
The helper makes one paginated Workflow list operation and no downstream calls.
If its FULL-view result already contains the fields needed for a selected
execution, do not describe that execution again. Use the exact description only
when the caller starts from an exact execution ID; after a helper listing, use
its FULL projection without a second API call.

## Expected output

For a listing: execution resource/ID, exact import name, state/error,
timestamps, revision, Batch job ID, scan/page counts, and truncation. For exact
description: the same execution's allowlisted argument/result, bounded error,
and current steps.

## Required bounds

For listing, always use a UTC time window, result limit, and scan limit. Return
at most 100 runs and scan at most 5,000 executions. For description, inspect one
exact execution only; do not list neighboring executions.

## Evidence to retain

Workflow resource, exact import identity, execution resource, state, revision,
Batch job ID, and scan/truncation metadata.

## Common failures

Missing Application Default Credentials, expired history, malformed arguments,
wrong Workflow, API quota, permission denied, missing result before Batch
creation, or scan truncation before enough matches.

## Related repository sources

The live historical Workflow revision and, when supplied, the sibling
`import/pipeline/workflow/import-automation-workflow.yaml` source.
