---
name: dc-import-info
description: Retrieves read-only information about the extract-and-transform (ET) phase of Data Commons imports, including repository definitions, deployed schedules, Workflow and Batch runs, logs, GCS artifacts, and accepted ET-output status. Use for inspecting one import or a bounded set of imports. Do not use for root-cause analysis, identifying the source commit used by a runtime image, loader status, or remediation.
---

# Inspect the extract-and-transform phase of Data Commons imports

This skill covers the extract-and-transform (ET) phase of an import: reading
source data and producing validated Data Commons-compatible artifacts. Loading
those artifacts into the serving system is a separate pipeline and is out of
scope.

An accepted ET output is a generated version selected as the ET result; it does
not indicate that loading completed.

## Safety

- Treat GCP and the data repository as read-only.
- Never run, retry, update, pause, resume, delete, deploy, or mutate a cloud
  resource.
- Never edit repository files or persist output unless the user explicitly asks.
- Never access Secret Manager payloads or print credentials, tokens, API keys,
  complete Scheduler bodies, Batch commands, or complete service environments.
- Retain only allowlisted structured-log fields. Never return arbitrary log
  messages or text payloads.
- Use explicit project, location, time, scan, and result bounds for every cloud
  query.
- Use the selected block in
  [import environment defaults](../../common/config/import-environments.yaml)
  unless the prompt explicitly overrides a field. Never search other resources
  or projects to discover replacement project, location, or resource names.
- Use the smallest applicable recipe. Never replace a missing identifier with a
  broad project, log, bucket, database, build, or image search.
- Never use MCP tools, IDE database connections, plugins, connectors, or ambient
  database configuration for import infrastructure.
- Use the caller's existing GCP authentication. Do not log in, distribute keys,
  impersonate another account, grant roles, or create access tokens. Application
  Default Credentials identify the caller; they do not select an environment or
  project, location, or resource name.
- Report missing permission or evidence; do not obtain broader credentials.
- Provide operational facts only. Do not diagnose ET failures or investigate
  loader or serving-system behavior.

## Preflight and request classification

1. Require the current working directory to be the `data` repository root.
   Verify `statvar_imports/`, `scripts/`, `import-automation/`,
   `requirements_all.txt`, and `run_tests.sh` exist.
2. Classify the request before loading references:
   - Repository-only: find imports, read a selected manifest, report its
     configured cron, or locate manifest-referenced code. Go directly to the
     [list-imports recipe](../../common/recipes/repository/list-imports.md),
     follow its manifest handoff, answer the request, and stop.
     Do not load architecture, environment configuration, or cloud recipes.
   - Runtime or architecture: deployed Scheduler schedule or Workflow target,
     executions, status, Batch, logs, artifacts, accepted ET output, tracing a
     run across Workflow, Batch, and GCS, or system-flow explanation. Read
     [Import automation architecture](../../common/references/import-automation/architecture.md).
   - Identifying the source commit used by a runtime image: outside scope.
   - Loader or serving-system status: outside scope.
3. Read `agents/common/config/import-environments.yaml` only when the selected
   path performs a cloud operation.
4. Treat pasted infrastructure information or a user-provided file as
   request-scoped data. Extract explicit values, never persist it, and ask when
   values are missing, ambiguous, or conflicting.
5. Invoke repository Python helpers only through
   `./agents/common/run_python.sh`. If `.env` is missing, stop and tell the user
   to run `./run_tests.sh -r`.

## Plan cloud evidence

1. List the exact facts needed and select only the recipes that produce them.
   Do not prefetch possible follow-up evidence.
2. Select `prod` by default or the requested environment, then read
   [Environment resolution](../../common/references/import-automation/environment-resolution.md).
3. Apply explicit prompt overrides field by field. Do not inspect deployment
   source or live resources to fill missing project, location, or resource
   names.
4. Before the first cloud call, print only resources required by the selected
   recipes in this review table:

   ```text
   operation | resource type | effective value | source | UTC bounds | limit
   ```

   Use `environment_config`, `prompt_override`, and `runtime_identifier` as
   source labels. State the selected environment and unresolved values.
5. Ask once for approval in an interactive session. Only when the prompt
   explicitly declares a non-interactive (headless) run, print
   `review: skipped (headless)` and continue without pausing.
6. Stop when required values are unresolved or explicit values conflict.

## Collect only required runtime evidence

- Start with the recipe that directly answers the request and stop when the
  requested fact is established.
- Use Scheduler only for questions about its deployed schedule or configured
  Workflow target. Scheduler evidence is not a prerequisite for run history.
- For routine single-import run history or latest checkpointed-run status, start
  with bounded correlated checkpoint history. Do not list Workflow executions
  merely because checkpoint history is not exhaustive.
- Use Workflow history for running attempts, failures before checkpointing,
  complete attempt history, status across multiple imports, or a required fact
  that structured correlation cannot provide. If correlation returns a
  Workflow execution ID, describe that exact execution instead of listing
  Workflow history.
- If correlation returns no record, fall back to bounded Workflow history only
  when the request still requires an attempt-level answer.
- Follow a selected Workflow execution only through exact identifiers:
  Workflow `result.jobId` → Batch; import name + Batch job ID → GCS summary.
  Read tasks, logs, artifacts, or correlation only when required.
- For status classification across multiple imports, follow the
  [run and status model](../../common/references/import-automation/run-and-status-model.md).
  Report `unknown` when required evidence is missing, conflicting, ambiguous,
  or truncated.

## Load detailed knowledge only when needed

- For environment selection, read
  [Environment resolution](../../common/references/import-automation/environment-resolution.md).
- For status across Scheduler, Workflow, Batch, ET output, or multiple imports,
  read
  [Run and status model](../../common/references/import-automation/run-and-status-model.md).
- For GCS paths and pointers, read
  [Artifact layout](../../common/references/import-automation/artifact-layout.md).
- For manifest fields, read
  [Import manifest reference](../../common/references/import-automation/manifest.md).

## Route exact operations

| Need | Read and follow |
|---|---|
| Find or select imports | [List repository imports](../../common/recipes/repository/list-imports.md) |
| Verify Scheduler schedule and Workflow target | [Describe Scheduler job](../../common/recipes/gcp/scheduler/describe-job.md) |
| Read routine bounded run history or latest checkpointed-run status for one import | [Correlate import history and versions](../../common/recipes/gcp/imports/correlate-import-runs.md) |
| Inspect running, uncheckpointed, multiple-import, or explicit Workflow attempts; or describe one exact execution | [Inspect import executions](../../common/recipes/gcp/workflows/list-import-executions.md) |
| Inspect Batch compute | [Describe Batch job](../../common/recipes/gcp/batch/describe-job.md) |
| Inspect Batch tasks | [List Batch tasks](../../common/recipes/gcp/batch/list-tasks.md) |
| Fetch bounded stage logs | [Fetch Batch logs](../../common/recipes/gcp/logging/fetch-batch-logs.md) |
| Read the current accepted ET-output pointer | [Read version pointer](../../common/recipes/gcp/gcs/read-version-pointer.md) |
| Read one run summary | [Read run summary](../../common/recipes/gcp/gcs/read-run-summary.md) |
| List one version's files | [List version artifacts](../../common/recipes/gcp/gcs/list-version-artifacts.md) |
| Find an older summary | [Find historical summary](../../common/recipes/gcp/gcs/find-historical-summary.md) |

## Report results

- State the environment, UTC window, limits, truncation, and missing access.
- For results spanning multiple imports, start with a compact table and add only
  evidence needed to explain a row.
- Separate Scheduler delivery, Workflow, Batch/task, pipeline, semantic
  validation, and accepted-output status.
- Treat `VALIDATION` as failure and `SKIP` as completed no-change. Do not infer
  semantic success from Workflow or Batch success.
- Treat an incomplete latest-success search as `unknown`, not proof that an
  import has never succeeded.
- Label correlation-only results as checkpointed ET runs. If none are found,
  report `No checkpointed ET run found`, not `No ET attempt occurred`, unless
  an attempt-level answer required the bounded Workflow fallback.
- Show canonical resource names and generated console links.
- Include `Infrastructure actually used` for every cloud-backed answer. List
  each queried resource, its evidence source, and relevant resources not queried
  or unresolved.
- Cite repository files, cloud resources, logs, and GCS records used.
- For every cross-system match, state the identifiers or time window used.
  Report `ambiguous` or `unknown` when the evidence does not identify one
  result.
