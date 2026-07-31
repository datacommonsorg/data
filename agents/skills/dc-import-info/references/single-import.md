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
3. If the request asks only for code, manifest, validation, or configured
   auto-refresh information, answer from local evidence and stop. Do not preview
   infrastructure or query GCP.
4. For a cloud-backed request, run the local preview with the intended UTC
   window, limits, environment, and explicit user-provided values:

   ```bash
   ./agents/common/run_python.sh \
     agents/common/import_support/collect_import_snapshot.py \
     --mode=single_import \
     --import_name=<IMPORT_NAME> \
     --environment=<ENVIRONMENT> \
     --start_time=<RFC3339_UTC> \
     --end_time=<RFC3339_UTC> \
     --run_limit=<LIMIT> \
     --preview_infrastructure
   ```

   Omit redundant production infrastructure flags. Include each explicit user
   selection and every required non-production coordinate.
5. Print the proposed values and sources. Ask once before cloud access in an
   interactive session. In a prompt-declared headless run, print
   `review: skipped (headless)` and continue only when `ready_for_cloud` is
   true.
6. After approval or headless review, rerun the exact command without
   `--preview_infrastructure` and add `--verbose`. Progress is written to stderr;
   the schema-valid snapshot remains on stdout.
7. Default to the latest ten matching Workflow executions within 90 days.
8. Present identity/code, configured and deployed auto-refresh state, resource
   links, latest run, latest semantic success, recent runs, actual artifacts,
   current state, version events, downstream ingestion events, pointers, and
   provenance confidence. If bounded Workflow and Spanner evidence do not
   contain a success, report the latest-success result as incomplete.
9. End with the exact Scheduler, Workflow, Batch, GCS, and Spanner resources
   actually used. Mark unresolved or skipped resources explicitly.

## Clarify instead of guessing

Ask the user when the Scheduler project/location cannot be resolved, more than
one live deployment matches, explicit sources conflict, or live evidence
conflicts with the selected scope. A missing resource or permission is a
result, not permission to search every project. Never use ambient or MCP-backed
infrastructure as a fallback.

## Do not diagnose

Report errors and failed stages as operational facts. Do not infer root cause,
recommend code changes, or weaken validation in this skill.
