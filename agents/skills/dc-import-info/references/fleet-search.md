# Fleet search

Use this path for bounded live operational questions about multiple imports.
For manifest-only name or configured cron queries, use repository catalog.

## Supported criteria

- UTC start/end time.
- Composite status: `failed`, `running`, `succeeded`, `skipped`, or `unknown`.
- Optional case-insensitive import-name substring.
- Minimum consecutive terminal semantic failures.

Default to production, the previous 24 hours, and at most 100 returned runs.
Report every scan and result limit.

## Procedure

1. Resolve production Workflow candidates from repository configuration or use
   explicit request-scoped infrastructure values.
2. Preview the Workflow resource, UTC window, scan limit, result limit, and any
   later evidence sources required for semantic classification. Follow the cloud
   approval gate in `SKILL.md`.
3. Use the Workflow execution recipe without `--absolute_import_name` to list
   FULL-view runs once for the bounded window. Apply the name filter locally.
4. Classify Workflow technical failures, active runs, and successful executions
   before reading any downstream system.
5. If the requested status requires pipeline semantics, fetch only a status
   source for technically successful candidate runs. Do not fetch Batch tasks,
   logs, general artifacts, ingestion history, or provenance merely to classify
   status.
6. When using current `ImportStatus`, require its job ID to match the selected
   Workflow result. Current rows cannot reconstruct overwritten history.
7. When using GCS, read an exact staging summary for the latest run or use the
   bounded historical-summary recipe. Return `unknown` for missing, ambiguous,
   or truncated correlation.
8. For consecutive failures, inspect runs newest first. Any result other than
   `failed`, including active, unknown, succeeded, or skipped, breaks the streak.
9. Return a compact table first. Add details only for rows necessary to explain
   the result, then print `Infrastructure actually used`.

## Status semantics

- `failed`: Workflow or Batch technical failure, or pipeline `VALIDATION` or
  failure.
- `running`: Workflow or Batch is active, queued, or running.
- `succeeded`: pipeline `STAGING` and publication are both observed.
- `skipped`: pipeline `SKIP`.
- `unknown`: required semantic evidence is missing or conflicting.

Never use MCP, IDE database connections, plugins, connectors, or ambient
database configuration. Never broaden the selected projects or time window to
compensate for missing access.
