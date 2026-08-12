---
name: dc-import-diagnostics
description: Inspects and troubleshoots the extract-and-transform (ET) phase of Data Commons imports. Use when a user asks about an import's configuration, schedule, status, recent output, or runtime behavior, or asks why an import failed, is stuck, or produced unexpected output. Do not use for loader or serving-system issues.
---

# Inspect and diagnose Data Commons import ET

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
- Report missing permission or evidence. Base diagnoses on cited evidence,
  state unknowns, and do not investigate loader or serving-system behavior.

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
   finalized versions, Batch, logs, artifacts, current ET output, or Batch
   source-commit evidence—read
   [Import automation architecture](../../common/references/import-automation/architecture.md).
4. For requests asking why an import failed, is stuck, or produced unexpected
   output, read and follow
   [Import troubleshooting](troubleshooting/troubleshooting.md). It selects the
   applicable information routes. Do not load troubleshooting guidance for
   factual inspection requests.
5. Treat complete attempt history, Workflow execution inspection, historical
   failures that produced no summary, loader status, and execution of
   remediation as unsupported by this skill.
6. Read `agents/common/config/import-environments.yaml` only when the selected
   route performs a cloud operation.
7. Invoke repository Python helpers only through
   `./agents/common/run_python.sh`. If a command, Python dependency, `.env`, or
   authentication prerequisite is missing, stop and direct the user to
   [agent dependency setup](../../dependency-setup.md). Do not run the readiness
   checker on every request, install dependencies, or initiate login.

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

## Select an operation

Use the smallest applicable operation from the route table. Linked recipes own
their required inputs, supported fields, defaults, bounds, and failure
behavior. For questions combining current status, GCS versions, and Batch
evidence, first read the
[import evidence flow](../../common/references/import-automation/import-evidence-flow.md).
Before selecting a runtime operation, apply the architecture's
[runtime terminology](../../common/references/import-automation/architecture.md#runtime-terminology).
Start `latest run`, `current run`, and `current status` with Cloud Spanner; do
not substitute finalized GCS evidence.

| Need | Read and follow |
|---|---|
| Find or select imports | [List repository imports](../../common/recipes/local/list-imports.md) |
| Verify deployed Scheduler schedule and Workflow target | [Describe Scheduler job](../../common/recipes/gcp/scheduler/describe-job.md) |
| Read the latest run, current run, or current status for one import; read an exact current version; or read bounded current snapshots across imports | [Query current import status](../../common/recipes/gcp/spanner/query-import-status.md) |
| List recent finalized versions, GCS paths, and Batch IDs | [List recent import summaries](../../common/recipes/gcp/gcs/list-import-summaries.md) |
| Read one supplied or selected version's summary | [Read version summary](../../common/recipes/gcp/gcs/read-version-summary.md) |
| Read the latest finalized candidate or accepted-output (last successful) version pointer | [Read version pointer](../../common/recipes/gcp/gcs/read-version-pointer.md) |
| List one selected version's files | [List version artifacts](../../common/recipes/gcp/gcs/list-version-artifacts.md) |
| Inspect one exact Batch job | [Describe Batch job](../../common/recipes/gcp/batch/describe-job.md) |
| Inspect tasks for one exact Batch job | [List Batch tasks](../../common/recipes/gcp/batch/list-tasks.md) |
| Fetch bounded structured logs for one exact Batch job | [Fetch Batch logs](../../common/recipes/gcp/logging/fetch-batch-logs.md) |
| Trace an exact Batch job to runtime-image or source-commit evidence, only when explicitly requested | [Trace Batch job to source commit](../../common/recipes/gcp/batch/trace-batch-job-source-commit.md) |

## Report evidence

- State the selected environment. For each operation, include applicable UTC
  bounds, result limit, truncation, and missing access.
- For results spanning imports, start with a compact table.
- Follow the evidence boundaries in
  [import evidence flow](../../common/references/import-automation/import-evidence-flow.md).
  Do not synthesize an overall status from separate evidence sources.
- Include `Infrastructure actually used` for every cloud-backed answer,
  identifying queried and unresolved resources.
- Cite the repository files, cloud resources, logs, and GCS objects used. State
  the exact identifier used for cross-system correlation; otherwise report
  `ambiguous` or `unknown`.
