# Single-import inspection

Use this path when the user supplies one globally unique `import_name`.

## Required input

- `import_name` exactly as stored in a manifest.
- Production unless the user requests another environment.
- Optional request-scoped infrastructure values pasted by the user or read from
  an exact user-provided path.

## Procedure

1. Resolve the name with the
   [resolve-import recipe](../../../common/recipes/repository/resolve-import.md).
2. Read the returned manifest and existing referenced source paths. Report zero
   or multiple matches; never choose a near match.
3. If the question is local-only, answer and stop without reviewing or querying
   cloud infrastructure.
4. For cloud-backed questions, write a minimal evidence plan. For example:
   - Deployment only: Scheduler description.
   - Last run: Scheduler verification and one matching Workflow execution.
   - Last ten runs: Scheduler verification and ten matching Workflow executions.
   - Current publication state: add one current Spanner query.
   - Selected run artifacts: add one version pointer or exact version listing.
5. Preview only the resources needed by that plan and follow the cloud approval
   gate in `SKILL.md`.
6. Invoke the selected recipes in dependency order. Stop as soon as the answer
   is supported.
7. Default a request for “the last run” to one matching execution within the
   previous 90 days. State when scan truncation makes that result incomplete.
8. For semantic status after Workflow success, use one source first:
   - Query current `ImportStatus` and accept it only if `JobId` matches; or
   - Read `staging_version.txt`, then its exact `import_summary.json`, and verify
     both import name and job ID.
9. Fetch Batch, tasks, logs, artifacts, ingestion history, or provenance only
   when the question requires those details.
10. End with `Infrastructure actually used`, including skipped and unresolved
    components.

## Clarify instead of guessing

Ask when Scheduler project/location cannot be resolved, more than one live
deployment matches, explicit sources conflict, or live evidence conflicts with
the selected scope. A missing resource or permission is a result, not permission
to search every project.

## Do not diagnose

Report errors and failed stages as operational facts. Do not infer root cause,
recommend code changes, or weaken validation in this skill.
