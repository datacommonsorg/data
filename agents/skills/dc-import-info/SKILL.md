---
name: dc-import-info
description: Retrieves read-only information about the extract-and-transform (ET) phase of Data Commons imports, including repository definitions, configured and deployed schedules, current ImportStatus state, recent finalized GCS versions, exact summaries, accepted-output pointers, and exact known Batch jobs, tasks, and logs. Use for inspecting one import or a bounded set of current import snapshots. Do not use for root-cause analysis, complete attempt history, runtime-image source provenance, loader status, or remediation.
---

# Inspect Data Commons import ET information

This skill covers extraction and transformation (ET): read source data,
transform and validate it, and produce Data Commons-compatible artifacts.
Loading an eligible output into the serving system is a separate pipeline and
is out of scope.

## Safety

- Treat GCP and the data repository as read-only.
- Never run, retry, update, pause, resume, delete, deploy, or mutate a cloud
  resource.
- Never edit repository files or persist output unless the user explicitly asks.
- Never access Secret Manager payloads or print credentials, tokens, API keys,
  complete Scheduler bodies, Batch commands, or complete service environments.
- Retain only allowlisted structured-log fields. Never return arbitrary log
  messages or text payloads.
- Bound every cloud operation by exact resources and explicit result limits;
  add UTC time bounds where the operation supports or requires them.
- Use the selected block in
  [import environment defaults](../../common/config/import-environments.yaml)
  unless the prompt explicitly overrides a field. Never search other projects
  or resources for replacements.
- Use the smallest applicable recipe. Never replace a missing identifier with a
  broad project, Workflow, Batch, log, bucket, database, build, or image search.
- Never use MCP tools, IDE database connections, plugins, connectors, or ambient
  database configuration for import infrastructure.
- Use the caller's existing GCP authentication. Do not log in, distribute keys,
  impersonate another account, grant roles, or create access tokens.
- Report missing permission or evidence. Provide facts only; do not diagnose a
  failure or investigate loader or serving-system behavior.

## Classify the request before loading context

1. Require the current working directory to be the `data` repository root.
   Verify `statvar_imports/`, `scripts/`, `import-automation/`,
   `requirements_all.txt`, and `run_tests.sh` exist.
2. For repository-only questions—find an import, read its manifest, report its
   configured cron, or locate manifest-referenced code—go directly to the
   [list-imports recipe](../../common/recipes/local/list-imports.md), read
   only the selected manifest or requested code, answer, and stop. Do not load
   architecture, environment configuration, or cloud recipes.
3. For architecture or runtime questions—deployed schedule, current status,
   finalized versions, Batch, logs, artifacts, or current ET output—read
   [Import automation architecture](../../common/references/import-automation/architecture.md).
4. Treat complete attempt history, Workflow execution inspection, historical
   failures that produced no summary, runtime-image source provenance, loader
   status, and remediation as unsupported by this skill.
5. Read `agents/common/config/import-environments.yaml` only when the selected
   route performs a cloud operation.
6. Invoke repository Python helpers only through
   `./agents/common/run_python.sh`. If `.env` is missing, stop and tell the user
   to run `./run_tests.sh -r`.

## Review cloud operations

1. Select only the recipes needed to answer the request. Do not prefetch
   possible follow-up evidence.
2. Select `prod` by default or the requested environment, then read
   [Environment resolution](../../common/references/import-automation/environment-resolution.md).
3. Apply explicit prompt overrides field by field. Do not inspect live resources
   to fill missing project, location, or resource names.
4. Before the first cloud call, print only the selected operations:

   ```text
   operation | resource type | effective value | source | UTC bounds | limit
   ```

   Use `environment_config`, `prompt_override`, and `runtime_identifier` as
   source labels. State unresolved values.
5. Ask once for approval in an interactive session. Only when the prompt
   explicitly declares a non-interactive run, print
   `review: skipped (headless)` and continue without pausing.
6. Stop when required values are unresolved or explicit values conflict.

## Select evidence by question

- Use Scheduler only for a deployed schedule or target question. The manifest
  cron is configured intent; the live Scheduler job is deployed state.
- Use the Cloud Spanner `ImportStatus` table only as a mutable current snapshot.
  Its raw `State` becomes `current_status`; its `JobId` is the ET Batch
  identifier. Never select or use `ImportStatus.WorkflowId`: it is loader-owned
  and may refer to an earlier run.
- For a query across imports, filter the current `ImportStatus` rows. A time
  window applies to `StatusUpdateTimestamp`; it does not reconstruct historical
  events. Unless the user supplies bounds, use production, the previous seven
  days, and at most 100 returned rows.
- Use the GCS summary-list helper for up to five recent finalized versions of
  one import. It scans at most 100 summary names and returns version, date, the
  exact GCS version URI, and Batch job ID. If the scan is truncated, return no
  history.
- GCS summary history is not attempt history. It includes only attempts that
  reached version-summary creation. A Batch failure before
  `import_summary.json` exists is absent; older such failures are unsupported.
- Read an exact summary when its classification or metrics are needed. Read the
  current-output pointer only when acceptance or currentness matters.
- Describe Batch, tasks, or logs only from an exact `ImportStatus.JobId` or
  selected summary `job_id`. Never list jobs to discover an identifier.
- Do not query database history tables or Workflow execution history.

## Load detailed references only when needed

- For current-state, finalized-version, artifact, or Batch navigation, read the
  [import evidence flow](../../common/references/import-automation/import-evidence-flow.md).
- For GCS paths, summaries, and pointers, read
  [artifact layout](../../common/references/import-automation/artifact-layout.md).
- For manifest fields, read the
  [import manifest reference](../../common/references/import-automation/manifest.md).

## Ground commands in recipes

Before presenting or executing a cloud or support command:

1. Select the operation from the route table.
2. Open and read its linked recipe during the current turn.
3. Use the recipe's command structure and literal resource or artifact names.
4. Resolve placeholders only from declared inputs or linked references.
5. If a required value remains unresolved, stop. Never reconstruct a command
   from memory or a generic cloud convention.

## Route exact operations

| Need | Read and follow |
|---|---|
| Find or select imports | [List repository imports](../../common/recipes/local/list-imports.md) |
| Verify deployed Scheduler schedule and Workflow target | [Describe Scheduler job](../../common/recipes/gcp/scheduler/describe-job.md) |
| Read current status for one import, exact current version, or bounded current snapshots across imports | [Query current import status](../../common/recipes/gcp/spanner/query-import-status.md) |
| List up to five recent finalized versions, GCS paths, and Batch IDs | [List recent import summaries](../../common/recipes/gcp/gcs/list-import-summaries.md) |
| Read one selected version's summary | [Read run summary](../../common/recipes/gcp/gcs/read-run-summary.md) |
| Read the current candidate or accepted-output pointer | [Read version pointer](../../common/recipes/gcp/gcs/read-version-pointer.md) |
| List one selected version's files | [List version artifacts](../../common/recipes/gcp/gcs/list-version-artifacts.md) |
| Inspect one exact Batch job | [Describe Batch job](../../common/recipes/gcp/batch/describe-job.md) |
| Inspect tasks for one exact Batch job | [List Batch tasks](../../common/recipes/gcp/batch/list-tasks.md) |
| Fetch bounded structured logs for one exact Batch job | [Fetch Batch logs](../../common/recipes/gcp/logging/fetch-batch-logs.md) |

## Report without merging unlike evidence

- State the environment, UTC window when used, limits, truncation, and missing
  access.
- For results spanning imports, start with a compact table.
- Report `current_status`, `summary_status`, `is_current`, and `batch_state` as
  separate fields. Do not synthesize an overall status.
- Define `is_current` as whether the selected version equals the current
  accepted ET-output pointer. It does not establish loader completion or
  serving availability.
- Treat `VALIDATION` as failed ET validation and `SKIP` as completed no-change.
  A `STAGING` summary means eligible for acceptance, not necessarily current.
- Label GCS-list results as finalized ET versions, not Workflow or Batch attempt
  history. If no summary exists, say that no finalized version was found within
  the bounded scan; do not say no attempt occurred.
- If a requested historical failure could have stopped before summary creation,
  report that the available GCS history cannot answer it.
- Include `Infrastructure actually used` for every cloud-backed answer, listing
  queried resources and relevant resources not queried or unresolved.
- Cite repository files, cloud resources, logs, and GCS objects used. For each
  cross-system match, state the exact identifier used; otherwise report
  `ambiguous` or `unknown`.
