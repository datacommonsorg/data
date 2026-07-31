---
name: dc-import-info
description: Retrieves read-only information about Data Commons imports, including code, manifests, auto-refresh configuration, cloud resources, artifacts, run history, and status. Use for inspecting one import or searching imports by operational criteria. Do not use for root-cause analysis or remediation.
---

# Inspect Data Commons imports

## Safety

- Treat GCP and the data repository as read-only.
- Never run, retry, update, pause, resume, delete, deploy, or mutate a cloud
  resource.
- Never edit repository files or persist a snapshot unless the user explicitly
  requests an output file.
- Never access Secret Manager payloads or print credentials, tokens, API keys,
  complete Scheduler bodies, Batch commands, or Cloud Run environments.
- Retain only allowlisted structured import stage/status log fields. Do not
  return arbitrary log messages or text payloads.
- Use explicit project, location, time, and result bounds for every cloud query.
- Use only repository-local helpers, their Python SDK clients, and documented
  bounded `gcloud` operations. Never use MCP tools, IDE database connections,
  plugins, connectors, or ambient database configuration for import
  infrastructure, even when they are available.
- Report missing permission or evidence; do not obtain broader credentials.
- Provide operational information only. If the user asks why an import failed
  or how to fix it, use `dc-import-debugging` when available.

## Preflight

1. Require the current working directory to be the `data` repository root.
   Verify `statvar_imports/`, `scripts/`, `import-automation/`,
   `requirements_all.txt`, and `run_tests.sh` exist.
2. Read [Import automation architecture](../../common/references/import-automation/architecture.md).
3. Treat pasted infrastructure information or a user-provided file as
   request-scoped data. Extract explicit values, never persist it, and ask when
   values are missing, ambiguous, or conflict with repository or live state.
4. Invoke Python only through `./agents/common/run_python.sh`. If `.env` is
   missing, stop and tell the user to run `./run_tests.sh -r`.

## Select the request mode

- For exactly one globally unique `import_name`, read
  [Single-import inspection](references/single-import.md).
- For manifest-only name or configured auto-refresh criteria, read
  [Repository catalog](references/repository-catalog.md).
- For imports matching execution time, operational state, or repeated-failure
  criteria, read [Fleet search](references/fleet-search.md).

## Gate cloud access

1. Classify the request before resolving infrastructure. Code, manifests,
   configured schedules, validation rules, and repository-catalog searches are
   local-only. Do not preview infrastructure or access GCP for those requests.
2. For a cloud-backed request, read
   [Environment resolution](../../common/references/import-automation/environment-resolution.md)
   and follow
   [Preview infrastructure](../../common/recipes/repository/preview-infrastructure.md).
3. Run the local preview with the same environment, explicit infrastructure,
   UTC window, and limits intended for collection. Print its proposed
   Scheduler, Workflow, GCS, helper, and Spanner values, source labels,
   unresolved fields, and blocked reads.
4. In an interactive session, ask once for approval and stop before the first
   cloud call. Continue only after approval.
5. Only when the prompt explicitly declares a headless run, print
   `review: skipped (headless)` and continue without pausing. Headless mode does
   not relax command permissions or permit guessing.
6. If `ready_for_cloud` is false, ask for missing values interactively. In a
   headless run, return a partial or blocked result without cloud access.
7. If explicit sources conflict, do not choose a flag value. If later live
   evidence conflicts with the selected scope, stop dependent reads and ask in
   an interactive session or return a partial result in headless mode.

## Common workflow

1. Resolve one exact import with `resolve_import.py`, or run a bounded local
   catalog query with `list_imports.py`. Scan only
   `statvar_imports/**/manifest.json` and `scripts/**/manifest.json`.
2. Read the selected manifest specification and referenced local source files.
   A cron schedule proves configured intent, not a deployed Scheduler job.
3. After the cloud gate, invoke the snapshot collector with the same arguments
   used for the preview, excluding `--preview_infrastructure`.
4. Verify the Scheduler job using its description and decoded
   `argument.importName`, then follow its HTTP target to the exact Workflow.
5. Treat one Workflow execution as one logical run. Join to Batch through
   `result.jobId` when available; otherwise verify bounded candidates using the
   full runnable import identity and record correlation confidence. If the
   Batch resource has expired, retain `result.jobId` and correlate a summary
   only when both its job ID and import name match.
6. Collect only requested Batch/task details, structured logs, actual GCS
   objects, version pointers, current Spanner state, accepted-version history,
   downstream ingestion history, and runtime provenance.
7. Build the versioned snapshot defined by
   `../../common/schemas/import_snapshot.schema.json` and summarize it in chat.

## Load detailed knowledge only when needed

- For environment selection or conflicts, read
  [Environment resolution](../../common/references/import-automation/environment-resolution.md).
- For component and semantic status, read
  [Run and status model](../../common/references/import-automation/run-and-status-model.md).
- For GCS files and version pointers, read
  [Artifact layout](../../common/references/import-automation/artifact-layout.md).
- For image, build, Workflow revision, or commit questions, read
  [Runtime provenance](../../common/references/import-automation/runtime-provenance.md).
- For access questions, read
  [Identity and access](../../common/references/import-automation/identity-and-access.md).

## Route exact operations

| Need | Read and follow |
|---|---|
| Resolve an import | [Resolve import](../../common/recipes/repository/resolve-import.md) |
| Search configured imports | [List repository imports](../../common/recipes/repository/list-imports.md) |
| Review cloud candidates | [Preview infrastructure](../../common/recipes/repository/preview-infrastructure.md) |
| Verify Scheduler and target | [Describe Scheduler job](../../common/recipes/gcp/scheduler/describe-job.md) |
| List exact logical runs | [List import executions](../../common/recipes/gcp/workflows/list-import-executions.md) |
| Inspect Batch and tasks | [Describe Batch job and tasks](../../common/recipes/gcp/batch/describe-job-and-tasks.md) |
| Fetch bounded stage logs | [Fetch Batch logs](../../common/recipes/gcp/logging/fetch-batch-logs.md) |
| Inspect actual artifacts | [Inspect run artifacts](../../common/recipes/gcp/gcs/inspect-run-artifacts.md) |
| Resolve helper coordinates | [Describe ingestion helper](../../common/recipes/gcp/cloud-run/describe-ingestion-helper.md) |
| Read Spanner state/history | [Read import records](../../common/recipes/gcp/spanner/read-import-records.md) |
| Recover runtime source | [Resolve runtime provenance](../../common/recipes/gcp/cloud-build/resolve-runtime-provenance.md) |

## Output rules

- State the environment, UTC window, limits, truncation, and missing access.
- Treat an incomplete latest-success result as unknown, not as proof that an
  import has never succeeded.
- Separate Scheduler delivery, Workflow, Batch/task, pipeline, semantic
  validation, publication, and downstream-ingestion status.
- Treat `VALIDATION` as a semantic failure and `SKIP` as a completed no-change
  result. Do not infer semantic success from Workflow or Batch success.
- Show canonical resource names and generated console links.
- For every cloud-backed answer, include an `Infrastructure actually used`
  section. List the exact Scheduler, Workflow, Batch, GCS, and Spanner resource
  names from the snapshot and their evidence sources. Mark each resource that
  was not queried or could not be resolved.
- Cite repository files, cloud resources, logs, and GCS/Spanner records used.
- Label correlations and runtime provenance as `exact`,
  `strongly_correlated`, `time_correlated`, `ambiguous`, or `unknown`.
