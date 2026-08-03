# List Workflow executions

Recipe ID: `gcp.workflows.list-import-executions`

## Use when

Listing refresh runs for one import or a bounded fleet window.

## Required inputs

Full Workflow resource, UTC start/end, result limit, scan limit, and optional
exact absolute import name.

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

For a fleet window, omit `--absolute_import_name`.

## Preferred invocation

Use this focused helper because the installed `gcloud workflows executions
list` command cannot request FULL view and therefore omits `argument.importName`.
The helper makes one paginated Workflow list operation and no downstream calls.

## Expected output

Execution resource/ID, exact import name, state/error, timestamps, revision,
Batch job ID, scan/page counts, and truncation.

## Required bounds

Always use a UTC time window, result limit, and scan limit. Return at most 100
runs and scan at most 5,000 executions.

## Evidence to retain

Workflow resource, exact import identity, execution resource, state, revision,
Batch job ID, and scan/truncation metadata.

## Common failures

Missing Application Default Credentials, expired history, malformed arguments,
API quota, permission denied, or scan truncation before enough matches.

## Related repository sources

The live historical Workflow revision and, when supplied, the sibling
`import/pipeline/workflow/import-automation-workflow.yaml` source.
