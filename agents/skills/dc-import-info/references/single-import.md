# Single-import inspection

Use this path when the user supplies one globally unique `import_name`.

## Required input

- `import_name` exactly as stored in a manifest.
- Production unless the user requests another environment.
- Optional request-scoped infrastructure values pasted by the user or read from
  an exact user-provided path.

## Procedure

1. Resolve the name:

   ```bash
   ./agents/common/run_python.sh \
     agents/common/import_support/resolve_import.py \
     --import_name=<IMPORT_NAME>
   ```

2. Read the returned manifest specification and existing referenced source
   paths. Report zero or multiple matches; never choose a near match.
3. Resolve the Scheduler project/location. For production, use repository
   defaults only as candidates and verify them live. For another environment,
   require explicit or canonically discoverable coordinates.
4. Collect a snapshot:

   ```bash
   ./agents/common/run_python.sh \
     agents/common/import_support/collect_import_snapshot.py \
     --mode=single_import \
     --import_name=<IMPORT_NAME> \
     --environment=<ENVIRONMENT> \
     --scheduler_project=<PROJECT> \
     --scheduler_location=<LOCATION> \
     --verbose
   ```

   Progress is written to stderr; the schema-valid snapshot remains on stdout.
5. Default to the latest ten matching Workflow executions within 90 days.
6. Present identity/code, configured and deployed auto-refresh state, resource
   links, latest run, latest semantic success, recent runs, actual artifacts,
   current state, version events, downstream ingestion events, pointers, and
   provenance confidence. If bounded Workflow and Spanner evidence do not
   contain a success, report the latest-success result as incomplete.

## Clarify instead of guessing

Ask the user when the Scheduler project/location cannot be resolved, more than
one live deployment matches, or user/repository/live values conflict. A missing
resource or permission is a result, not permission to search every project.

## Do not diagnose

Report errors and failed stages as operational facts. Do not infer root cause,
recommend code changes, or weaken validation in this skill.
