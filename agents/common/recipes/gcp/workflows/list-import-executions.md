# List Workflow executions for one import

Recipe ID: `gcp.workflows.list-import-executions`

## Use when

Collecting logical refresh history or grouping fleet runs by exact import.

## Required inputs

Full Workflow resource, exact absolute import name, UTC start/end, result
limit, and scan limit.

## Clarify when

The Scheduler target cannot identify exactly one Workflow.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/import_support/list_import_runs.py \
  --workflow_resource=<FULL_RESOURCE> \
  --absolute_import_name=<DIRECTORY:IMPORT_NAME> \
  --start_time=<RFC3339_UTC> \
  --end_time=<RFC3339_UTC> \
  --run_limit=10
```

## Preferred invocation

Use the helper. It requests FULL execution view, paginates, parses the JSON
argument, and filters exact `argument.importName` locally.

## Expected output

Execution resource, state/error, timestamps, revision, parsed argument,
successful result/job ID, scan count, and truncation.

## Required bounds

Always use a UTC time window, result limit, and execution scan limit.

## Evidence to retain

Workflow resource/revision, execution resource, exact import match, result job
ID, and page/scan metadata.

## Common failures

Missing Application Default Credentials, expired execution history, malformed
argument/result, API quota, or scan truncation before enough matches.

## Related repository sources

The live historical Workflow revision and, when supplied, the sibling
`import/pipeline/workflow/import-automation-workflow.yaml` source.
