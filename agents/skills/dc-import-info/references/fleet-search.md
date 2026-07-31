# Fleet search

Use this path for bounded live operational questions about multiple imports.
For manifest-only name or configured cron queries, use repository catalog
instead.

## Supported criteria

- UTC start/end time.
- Composite status: `failed`, `running`, `succeeded`, `skipped`, or `unknown`.
- Optional case-insensitive import-name substring combined with live criteria.
- Minimum consecutive terminal semantic failures.

Default to production, the previous 24 hours, and at most 100 imports. If the
user asks for a broader search, retain the collector hard limits and report
truncation.

## Procedure

1. Resolve the selected environment and exact Scheduler/Workflow coordinates.
2. Build the manifest catalog once.
3. List Workflow executions once for the bounded window using FULL view, parse
   `argument.importName`, and group locally by exact import identity.
4. Apply the name criterion first. Collect verified Batch/GCS status evidence,
   then apply status and repeated-failure criteria before fetching detailed
   logs, runtime provenance, and Spanner history.
5. Collect a snapshot:

   ```bash
   ./agents/common/run_python.sh \
     agents/common/import_support/collect_import_snapshot.py \
     --mode=fleet \
     --environment=<ENVIRONMENT> \
     --scheduler_project=<PROJECT> \
     --scheduler_location=<LOCATION> \
     --start_time=<RFC3339_UTC> \
     --end_time=<RFC3339_UTC> \
     --status=<STATUS> \
     --verbose
   ```

   Progress is written to stderr; the schema-valid snapshot remains on stdout.
6. Return a compact table first, then details only for imports needed to answer
   the question. State scan/result limits and whether data was truncated.

## Status semantics

- `failed`: Workflow/Batch technical failure or pipeline `VALIDATION`/failure.
- `running`: Workflow or Batch is active, queued, or running.
- `succeeded`: pipeline `STAGING` and publication are both observed.
- `skipped`: pipeline `SKIP`.
- `unknown`: required semantic evidence is missing or conflicting.

For consecutive failure, inspect runs newest first. Any result other than
`failed`, including active, unknown, succeeded, or skipped, breaks the streak.
Never count across a gap in observed failures.
