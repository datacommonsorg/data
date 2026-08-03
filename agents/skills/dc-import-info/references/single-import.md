# Single-import inspection

Use this path when the user supplies one import name or name-like query.

## Required input

- An import name query.
- Production unless the user requests another environment.
- Optional request-scoped infrastructure values pasted by the user or read from
  an exact user-provided path.

## Procedure

1. Find the import with the
   [list-imports recipe](../../../common/recipes/repository/list-imports.md),
   using `--query=<IMPORT_NAME_QUERY> --limit=5`.
2. Automatically select a unique exact or case-insensitive exact result. For a
   prefix, substring, or fuzzy result, use the user's context and clarify when
   multiple candidates remain plausible. Report an empty result without
   guessing.
3. Read the selected manifest and choose the specification whose case-sensitive
   `import_name` matches the result. Use the
   [import manifest reference](../../../common/references/import-automation/manifest.md)
   before interpreting its fields.
4. If the question is local-only, answer and stop without reviewing or querying
   cloud infrastructure.
5. For cloud-backed questions, write a minimal evidence plan. For example:
   - Deployment only: Scheduler description.
   - Last run: Scheduler verification and one matching Workflow execution.
   - Last ten runs: Scheduler verification and ten matching Workflow executions.
   - Current publication state: add one current Spanner query.
   - Selected run artifacts: add one version pointer or exact version listing.
6. Load the selected environment from
   `agents/common/config/import-environments.yaml`, apply explicit prompt
   overrides field by field, preview only the resources needed by the plan, and
   follow the cloud approval gate in `SKILL.md`.
7. Invoke the selected recipes in dependency order. Stop as soon as the answer
   is supported.
8. Default a request for “the last run” to one matching execution within the
   previous 90 days. State when scan truncation makes that result incomplete.
9. For semantic status after Workflow success, use one source first:
   - Query current `ImportStatus` and accept it only if `JobId` matches; or
   - Read `staging_version.txt`, then its exact `import_summary.json`, and verify
     both import name and job ID.
10. For bounded version history or correlation of one known version, use the
    [correlate import runs recipe](../../../common/recipes/gcp/imports/correlate-import-runs.md).
    Use `import_history` when the import is the entry point and
    `import_version` when the version is already known. This correlation does
    not replace Workflow history for attempts that failed before version
    metadata was written. Treat its returned Workflow, Batch, and GCS values as
    ET glue; invoke their detail recipes only when the question requires more.
    State the effective limit and optional UTC range from the invocation with
    the result because the minimal JSON does not repeat them.
11. Fetch Batch, tasks, logs, artifacts, ingestion history, or provenance only
   when the question requires those details.
12. End with `Infrastructure actually used`, including skipped and unresolved
    components.

## Clarify instead of guessing

Ask when a required environment field is missing, explicit prompt values
conflict, or live evidence points outside the effective scope. A missing
resource or permission is a result, not permission to search every project.

## Do not diagnose

Report errors and failed stages as operational facts. Do not infer root cause,
recommend code changes, or weaken validation in this skill.
