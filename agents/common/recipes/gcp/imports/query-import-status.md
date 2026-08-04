# Query the current import-status snapshot

Recipe ID: `gcp.imports.query-import-status`

## Use when

The current mutable snapshot is needed for one import, or a bounded query must
find imports whose current state was updated in a time window. A current failure
can exist here even when the attempt produced no GCS summary.

## Required inputs

Spanner project, instance, and database from the effective environment. For one
import, the exact absolute import name and its simple manifest `import_name`.
For an across-import query, an inclusive UTC start, exclusive UTC end, result
limit, and optional exact raw `State` value.

## Clarify when

The import identity, environment, time window, state, or limit is unresolved or
conflicting.

## Read-only operation

Validate all substituted values first. Project, instance, and database values
must match `^[A-Za-z0-9][A-Za-z0-9._-]*$`. Absolute import names must match
`^[A-Za-z0-9_/-]+:[A-Za-z0-9_-]+$`; simple names must match
`^[A-Za-z0-9_-]+$`; timestamps must be UTC RFC3339 with start before end;
`State` must match `^[A-Z_]+$`; limits must be integers from 1 through 100.
Use the exact validated environment resource names as separately shell-quoted
`gcloud` arguments. Never insert arbitrary prompt text into SQL.

For one import, query both identity forms because stored rows can use the
absolute or simple name:

```bash
gcloud spanner databases execute-sql '<DATABASE>' \
  --instance='<INSTANCE>' \
  --project='<PROJECT>' \
  --sql="SELECT ImportName, State, JobId, LatestVersion, StatusUpdateTimestamp, ExecutionTime, DataVolume, NextRefreshTimestamp FROM ImportStatus WHERE ImportName IN ('<ABSOLUTE_IMPORT_NAME>', '<SIMPLE_IMPORT_NAME>') ORDER BY StatusUpdateTimestamp DESC LIMIT 2" \
  --format=json
```

For current snapshots updated in a bounded window, request one extra row to
detect truncation. Add `AND State = '<STATE>'` only for an exact state filter:

```bash
gcloud spanner databases execute-sql '<DATABASE>' \
  --instance='<INSTANCE>' \
  --project='<PROJECT>' \
  --sql="SELECT ImportName, State, JobId, LatestVersion, StatusUpdateTimestamp, ExecutionTime, DataVolume, NextRefreshTimestamp FROM ImportStatus WHERE StatusUpdateTimestamp >= TIMESTAMP('<START_RFC3339_UTC>') AND StatusUpdateTimestamp < TIMESTAMP('<END_RFC3339_UTC>') ORDER BY StatusUpdateTimestamp DESC, ImportName LIMIT <LIMIT_PLUS_ONE>" \
  --format=json
```

## Preferred invocation

Use the exact-import query for “current status.” Use the bounded query for
questions such as “which imports are currently failed and were updated in the
last week.” If no bounds are given, use production, the previous seven days,
and at most 100 returned rows.

This query returns current rows, not historical events. A row that failed and
later changed state no longer appears as failed. Do not claim the result lists
all failures that occurred in the window.

Never select, return, or follow `ImportStatus.WorkflowId`. It is loader-owned,
may belong to an earlier loader run, and is not the ET Workflow execution ID.
Use `JobId` only as the exact ET Batch identifier.

## Expected output

Separate fields for `current_status` (raw `State`), ET Batch `job_id`, recorded
latest version, status-update time, execution time, data volume, and next
refresh. Retain the stored `ImportName`; if both identity forms return rows,
report ambiguity rather than silently choosing one.

## Required bounds

The exact-import query is limited to two identity candidates. An across-import
query requires a start-inclusive, end-exclusive UTC window and returns at most
100 requested rows. Query `LIMIT_PLUS_ONE`, return only `LIMIT`, and report
truncation when the extra row exists.

## Evidence to retain

Database resource, query purpose, identity or UTC bounds, requested limit,
truncation, `current_status`, `JobId`, `LatestVersion`, and
`StatusUpdateTimestamp`.

## Common failures

Permission denied, schema drift, invalid placeholder substitution, no current
snapshot, duplicate identity forms, or a current row whose recorded version no
longer matches a GCS pointer.

## Related repository sources

[Run and status model](../../../references/import-automation/run-and-status-model.md),
[read one run summary](../gcs/read-run-summary.md), and
[read one version pointer](../gcs/read-version-pointer.md).
