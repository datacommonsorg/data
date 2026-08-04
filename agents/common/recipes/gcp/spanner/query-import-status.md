# Query the current import-status snapshot

Recipe ID: `gcp.spanner.query-import-status`

## Use when

The current mutable snapshot is needed by import name or exact current version,
or a bounded query must find current imports updated in a time window.
`ImportStatus` is a Cloud Spanner table keyed by `ImportName`. A current failure
can exist here even when the attempt produced no GCS summary.

## Required inputs

Spanner project, instance, and database from the effective environment, plus
the inputs for exactly one query form:

- exact import: absolute import name and simple manifest `import_name`;
- exact version: full exact `gcs_version_uri`;
- current snapshots: inclusive UTC start, exclusive UTC end, result limit, and
  optional exact raw `State`.

## Clarify when

The query form, environment, identity, exact version URI, time window, state,
or limit is unresolved or conflicting. A bare version name is insufficient for
an exact-version query.

## Read-only operation

Validate all substituted values first. Project, instance, and database values
must match `^[A-Za-z0-9][A-Za-z0-9._-]*$`. Absolute import names must match
`^[A-Za-z0-9_/-]+:[A-Za-z0-9_-]+$`; simple names must match
`^[A-Za-z0-9_-]+$`; a GCS version URI must match
`^gs://[a-z0-9][a-z0-9._-]*/[A-Za-z0-9_./-]+$`; timestamps must be UTC
RFC3339 with start before end; `State` must match `^[A-Z_]+$`; and limits must
be integers from 1 through 100. Use validated values as separately
shell-quoted `gcloud` arguments. Never insert arbitrary prompt text into SQL.

For one import, query both identity forms because stored rows can use the
absolute or simple name:

```bash
gcloud spanner databases execute-sql '<DATABASE>' \
  --instance='<INSTANCE>' \
  --project='<PROJECT>' \
  --sql="SELECT ImportName, State, JobId, LatestVersion, StatusUpdateTimestamp, DataImportTimestamp, ExecutionTime, DataVolume, NextRefreshTimestamp FROM ImportStatus WHERE ImportName IN ('<ABSOLUTE_IMPORT_NAME>', '<SIMPLE_IMPORT_NAME>') ORDER BY StatusUpdateTimestamp DESC LIMIT 2" \
  --format=json
```

For a full exact version URI, reverse-lookup only current snapshots:

```bash
gcloud spanner databases execute-sql '<DATABASE>' \
  --instance='<INSTANCE>' \
  --project='<PROJECT>' \
  --sql="SELECT ImportName, State, JobId, LatestVersion, StatusUpdateTimestamp, DataImportTimestamp, ExecutionTime, DataVolume, NextRefreshTimestamp FROM ImportStatus WHERE LatestVersion = '<GCS_VERSION_URI>' ORDER BY StatusUpdateTimestamp DESC, ImportName LIMIT 2" \
  --format=json
```

For current snapshots updated in a bounded window, request one extra row to
detect truncation:

```bash
gcloud spanner databases execute-sql '<DATABASE>' \
  --instance='<INSTANCE>' \
  --project='<PROJECT>' \
  --sql="SELECT ImportName, State, JobId, LatestVersion, StatusUpdateTimestamp, DataImportTimestamp, ExecutionTime, DataVolume, NextRefreshTimestamp FROM ImportStatus WHERE StatusUpdateTimestamp >= TIMESTAMP('<START_RFC3339_UTC>') AND StatusUpdateTimestamp < TIMESTAMP('<END_RFC3339_UTC>') ORDER BY StatusUpdateTimestamp DESC, ImportName LIMIT <LIMIT_PLUS_ONE>" \
  --format=json
```

For an exact state filter, add only the validated predicate
`AND State = '<STATE>'` immediately before `ORDER BY`. Do not run a state-only
query without the UTC window.

## Preferred invocation

Use the exact-import query for current status. Use the exact-version query only
to find a current row whose `LatestVersion` equals the complete GCS URI; it is
not version history and must not use a bare version or substring. Use the
bounded query for questions such as “which imports are currently failed and
were updated in the last week.” If no bounds are given, use production, the
previous seven days, and at most 100 returned rows.

These are current rows, not historical events. A row that failed and later
changed state no longer appears as failed. Do not claim the result lists all
failures that occurred in the window.

`StatusUpdateTimestamp` records the last change to the shared current row and
drives current-snapshot window queries. `DataImportTimestamp` records when a
`STAGING` ET result was written; it is not a general attempt timestamp.

Never select, return, or follow `ImportStatus.WorkflowId`. It is loader-owned,
may belong to an earlier loader run, and is not the ET Workflow execution ID.
Use `JobId` only as the exact ET Batch identifier.

Open a linked GCS or Batch recipe only if the requested fact requires that
additional operation; never run it automatically.

## Expected output

Separate fields for `current_status` (raw `State`), ET Batch `job_id`, recorded
latest version, status-update time, data-import time, execution time, data
volume, and next refresh. Retain the stored `ImportName`; if an exact query
returns multiple rows, report ambiguity rather than silently choosing one.

## Required bounds

Exact-import and exact-version queries return at most two rows. An
across-import query requires a start-inclusive, end-exclusive UTC window and
returns at most 100 requested rows. Query `LIMIT_PLUS_ONE`, return only
`LIMIT`, and report truncation when the extra row exists.

## Evidence to retain

Database resource, query purpose, exact identity/version or UTC bounds,
requested limit, truncation, `current_status`, `JobId`, `LatestVersion`,
`StatusUpdateTimestamp`, and `DataImportTimestamp`.

## Common failures

Permission denied, schema drift, invalid placeholder substitution, no current
snapshot, duplicate identity forms, multiple current rows for one version, or
a recorded version that no longer matches a GCS pointer.

## Related repository sources

[Import evidence flow](../../../references/import-automation/import-evidence-flow.md),
[read one version summary](../gcs/read-version-summary.md),
[read one version pointer](../gcs/read-version-pointer.md), and
[describe one Batch job](../batch/describe-job.md).
