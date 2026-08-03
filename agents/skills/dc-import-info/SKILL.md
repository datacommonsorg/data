---
name: dc-import-info
description: Retrieves read-only information about Data Commons imports, including code, manifests, auto-refresh configuration, cloud resources, artifacts, run history, and status. Use for inspecting one import or searching imports by operational criteria. Do not use for root-cause analysis or remediation.
---

# Inspect Data Commons imports

## Safety

- Treat GCP and the data repository as read-only.
- Never run, retry, update, pause, resume, delete, deploy, or mutate a cloud
  resource.
- Never edit repository files or persist output unless the user explicitly asks.
- Never access Secret Manager payloads or print credentials, tokens, API keys,
  complete Scheduler bodies, Batch commands, or complete service environments.
- Retain only allowlisted structured log fields. Never return arbitrary log
  messages or text payloads.
- Use explicit project, location, time, and result bounds for every cloud query.
- Use the smallest applicable recipe. Never replace a missing identifier with a
  broad project, log, build, bucket, or database search.
- Never use MCP tools, IDE database connections, plugins, connectors, or ambient
  database configuration for import infrastructure.
- Report missing permission or evidence; do not obtain broader credentials.
- Provide operational information only. Route diagnosis and remediation to
  `dc-import-debugging` when available.

## Preflight

1. Require the current working directory to be the `data` repository root.
   Verify `statvar_imports/`, `scripts/`, `import-automation/`,
   `requirements_all.txt`, and `run_tests.sh` exist.
2. Read [Import automation architecture](../../common/references/import-automation/architecture.md).
3. Treat pasted infrastructure information or a user-provided file as
   request-scoped data. Extract explicit values, never persist it, and ask when
   values are missing, ambiguous, or conflicting.
4. Invoke repository Python helpers only through
   `./agents/common/run_python.sh`. If `.env` is missing, stop and tell the user
   to run `./run_tests.sh -r`.

## Select the request path

- For one import name or name-like query, read
  [Single-import inspection](references/single-import.md).
- For manifest-only searches, read
  [Repository catalog](references/repository-catalog.md).
- For imports matching execution time, status, or repeated-failure criteria,
  read [Fleet search](references/fleet-search.md).

## Plan evidence before cloud access

1. List the exact facts needed to answer the question.
2. Select only the recipes that produce those facts. Do not prefetch possible
   follow-up evidence.
3. Keep code, manifest, configured schedule, validation, and repository catalog
   requests local-only.
4. For cloud-backed requests, read
   [Environment resolution](../../common/references/import-automation/environment-resolution.md)
   and follow
   [Preview infrastructure](../../common/recipes/repository/preview-infrastructure.md).
5. Print the environment, resource candidates and sources, planned operations,
   UTC window, and limits before the first cloud call. Include only resources
   required by the selected recipes.
6. Ask once for approval in an interactive session. Only when the prompt
   explicitly declares a headless run, print `review: skipped (headless)` and
   continue without pausing.
7. Never guess unresolved non-production coordinates or choose between
   conflicting explicit values.

## Collect incrementally

1. Find imports with a bounded `list_imports.py --query` catalog query and
   select or clarify candidates according to its match strategy.
2. Read the selected manifest and referenced local files. Use the
   [import manifest reference](../../common/references/import-automation/manifest.md)
   before interpreting fields. A cron schedule proves configured intent, not a
   deployed Scheduler job.
3. Verify deployment with the exact Scheduler description and decoded
   `argument.importName`, then follow its target to the exact Workflow.
4. Treat one Workflow execution as one logical run. Use the bounded FULL-view
   Workflow helper because `gcloud workflows executions list` omits arguments.
5. Stop when the selected evidence answers the question. In particular:
   - Do not read Batch for Workflow-only history.
   - Do not read logs unless a selected run needs stage evidence.
   - Do not read GCS objects unless status, pointers, or artifacts are needed.
   - Do not read Spanner unless current publication, version, or ingestion state
     is needed.
   - Do not query Cloud Build unless runtime provenance is requested.
6. Join a selected run to Batch through Workflow `result.jobId`. Correlate GCS
   summaries only when both import and job identifiers match.
7. For a successful Workflow requiring semantic status, prefer one matching
   current Spanner row or the staging pointer plus its exact summary. Do not read
   both unless the first source is missing or conflicting.
8. Return `unknown` when historical semantic evidence cannot be correlated
   without a broad search.

## Load detailed knowledge only when needed

- For environment selection, read
  [Environment resolution](../../common/references/import-automation/environment-resolution.md).
- For component and composite status, read
  [Run and status model](../../common/references/import-automation/run-and-status-model.md).
- For GCS paths and pointers, read
  [Artifact layout](../../common/references/import-automation/artifact-layout.md).
- For commit questions, read
  [Runtime provenance](../../common/references/import-automation/runtime-provenance.md).
- For permissions, read
  [Identity and access](../../common/references/import-automation/identity-and-access.md).
- For manifest fields, read
  [Import manifest reference](../../common/references/import-automation/manifest.md).

## Route exact operations

| Need | Read and follow |
|---|---|
| Find or select imports | [List repository imports](../../common/recipes/repository/list-imports.md) |
| Review cloud candidates | [Preview infrastructure](../../common/recipes/repository/preview-infrastructure.md) |
| Verify Scheduler and target | [Describe Scheduler job](../../common/recipes/gcp/scheduler/describe-job.md) |
| List logical runs | [List import executions](../../common/recipes/gcp/workflows/list-import-executions.md) |
| Describe one run | [Describe Workflow execution](../../common/recipes/gcp/workflows/describe-execution.md) |
| Inspect Batch compute | [Describe Batch job](../../common/recipes/gcp/batch/describe-job.md) |
| Inspect Batch tasks | [List Batch tasks](../../common/recipes/gcp/batch/list-tasks.md) |
| Fetch bounded stage logs | [Fetch Batch logs](../../common/recipes/gcp/logging/fetch-batch-logs.md) |
| Read a version pointer | [Read version pointer](../../common/recipes/gcp/gcs/read-version-pointer.md) |
| Read one run summary | [Read run summary](../../common/recipes/gcp/gcs/read-run-summary.md) |
| List one version's files | [List version artifacts](../../common/recipes/gcp/gcs/list-version-artifacts.md) |
| Find an older summary | [Find historical summary](../../common/recipes/gcp/gcs/find-historical-summary.md) |
| Resolve Spanner coordinates | [Describe ingestion helper](../../common/recipes/gcp/cloud-run/describe-ingestion-helper.md) |
| Read one Spanner record type | [Read import records](../../common/recipes/gcp/spanner/read-import-records.md) |
| Recover runtime source | [Resolve runtime provenance](../../common/recipes/gcp/cloud-build/resolve-runtime-provenance.md) |

## Report results

- State the environment, UTC window, limits, truncation, and missing access.
- Separate Scheduler delivery, Workflow, Batch/task, pipeline, semantic
  validation, publication, and downstream-ingestion status.
- Treat `VALIDATION` as failure and `SKIP` as completed no-change. Do not infer
  semantic success from Workflow or Batch success.
- Treat an incomplete latest-success search as unknown, not proof that an import
  has never succeeded.
- Show canonical resource names and generated console links.
- Include `Infrastructure actually used` for every cloud-backed answer. List
  each queried resource, its evidence source, and every relevant resource not
  queried or unresolved.
- Cite repository files, cloud resources, logs, and GCS or Spanner records used.
- Label correlations and provenance as `exact`, `strongly_correlated`,
  `time_correlated`, `ambiguous`, or `unknown`.
