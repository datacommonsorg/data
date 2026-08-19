---
name: dc-import-diagnostics
description: Inspects and troubleshoots the extract-and-transform (ET) phase of Data Commons imports. Use when a user asks about an import's configuration, schedule, status, recent output, or runtime behavior, or asks why an import failed, is stuck, or produced unexpected output. Do not use for loader or serving-system issues.
---

# Inspect and diagnose Data Commons import ET

This skill covers extraction and transformation (ET): read source data,
transform and validate it, and produce Data Commons-compatible artifacts.
Loading an eligible output into the serving system is a separate pipeline and
is out of scope.

## Inputs resolved when needed

- Prefer values supplied by the user.
- Resolve other values only when needed.
- Use each input name as its placeholder throughout the skill.

| Input | Resolution |
|---|---|
| `<IMPORT_REPO>` | Use the supplied path. Otherwise, when needed, shallow-clone `datacommonsorg/import` with depth 1 into a temporary directory. |

## Safety

- Treat GCP and the data repository as read-only.
- Never run, retry, update, pause, resume, delete, deploy, or mutate a cloud
  resource.
- If a short-lived BigQuery table would help, give the user the exact
  command using
  [create_short_lived_bq_table.sh](scripts/create_short_lived_bq_table.sh).
  Use its `--help` option for usage. Ask the user to run the table-creating
  command and return the full table name. Never run that command yourself or
  delete any table.
- Never edit repository files or persist output unless the user explicitly asks.
- Ask before downloading or installing any library, command-line tool, browser
  binary, or executable, except for the repository dependency refresh below.
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
- Use the smallest applicable operation. Never replace a missing identifier
  with a broad project, Workflow, Batch, log, bucket, database, build, or image
  search.
- Never use MCP tools, IDE database connections, plugins, connectors, or ambient
  database configuration for import infrastructure.
- Use the caller's existing GCP authentication. Do not log in, distribute keys,
  impersonate another account, grant roles, or create access tokens.
- Report missing permission or evidence. Base diagnoses on cited evidence,
  state unknowns, and do not investigate loader or serving-system behavior.

## Important: Python execution

- Use a user-provided Python environment when supplied. Otherwise, use the
  repository-local Python virtual environment at `.env/`.
- With the repository environment:
  - Run helper scripts with `./agents/common/run_python.sh`.
  - Run tests with `./run_tests.sh -p <directory>`.
  - Run other Python commands with `.env/bin/python`.
  - If dependencies are missing or stale, run `./run_tests.sh -r`, then retry.
- Before running an import script, install its `requirements.txt`, if present.
  Ask before installing dependencies.
- Report an unusable environment. Never fall back to global `python` or
  `python3`.

## Classify the request before loading context

1. Require the current working directory to be the `data` repository root.
   Verify `statvar_imports/`, `scripts/`, `import-automation/`,
   `requirements_all.txt`, and `run_tests.sh` exist.
2. For repository-only questions—find an import, read its manifest, report its
   configured cron, or locate manifest-referenced code—go directly to the
   [repository import operations](references/imports.md), read
   only the selected manifest or requested code, answer, and stop. Do not load
   architecture, environment configuration, or cloud operational references.
3. For questions about the ET lifecycle, evidence boundaries, the relationship
   between attempts, versions, and accepted output, or multiple runtime
   evidence sources, read
   [Import automation architecture](../../common/references/import-automation/architecture.md).
   For a direct
   factual request with an unambiguous operation below, use that route without
   loading the architecture reference.
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
7. If a required command or authentication prerequisite is missing, stop and
   direct the user to
   [agent dependency setup](../../dependency-setup.md). Do not run the
   readiness checker on every request or initiate login.

## Review cloud configuration

1. Resolve prompt overrides first; otherwise use the selected block in
   [import environment defaults](../../common/config/import-environments.yaml).
   Ask if a required value is ambiguous, conflicting, or unresolved. Do not
   guess.
2. Before the first cloud call, show the configuration source, effective
   values, and bounded operations. Proceed with defaults; confirm overrides
   once.
3. Reuse the same configuration for subsequent read-only operations without
   further approval. Repeat the review only if the configuration changes.

## Load detailed references only when needed

- For current-status, recent-version, artifact, or Batch navigation, read the
  [import evidence flow](references/import-evidence-flow.md).
- For GCS version paths, summaries, and artifact names, read
  [artifact layout](../../common/references/import-automation/artifact-layout.md).
- For manifest fields, read the
  [import manifest reference](../../common/references/import-automation/manifest.md).

## Select an operation

- For cloud commands and reusable support workflows, use the smallest
  applicable route and its linked reference.
- Stop when a required input is unresolved.
- Keep short, conventional, read-only diagnostic actions inline when their
  target, scope, and stopping condition are clear.

For questions combining current status, GCS versions, and Batch evidence,
first read the
[import evidence flow](references/import-evidence-flow.md).

Treat a run or attempt as an execution. Treat a version as output that produced
an import summary. Route explicit wording using the table below. Ask for
clarification rather than assuming when the user does not distinguish a run
from a version or does not identify whether a version is from the current
attempt, the most recent summary, or the last successful output.

| Need | Read and follow |
|---|---|
| Find or select imports | [List repository-configured Data Commons imports](references/imports.md) |
| Verify deployed Scheduler schedule and Workflow target | [Describe and verify a Scheduler job](references/scheduler.md) |
| Read current status, the current or latest run or attempt, or the version recorded for the current attempt; or read bounded current snapshots across imports | [Query the current import-status snapshot](references/spanner.md) |
| List recent or latest import versions, GCS paths, and Batch IDs | [List recent import versions](references/gcs.md) |
| Read one supplied or selected version's summary | [Read one import version summary](references/gcs.md) |
| Find the last successful or accepted import version | [Find the last successful import version](references/gcs.md) |
| Compare a current or selected import version with the last successful version | [Compare an import version with the last successful version](references/import-evidence-flow.md) |
| List one selected version's files | [List artifacts for one import version](references/gcs.md) |
| Inspect one exact Batch job | [Describe one Batch job](references/batch.md) |
| Inspect tasks for one exact Batch job | [List tasks for one Batch job](references/batch.md) |
| Fetch bounded structured logs for one exact Batch job | [Fetch bounded Batch logs](references/batch.md) |
| Trace an exact Batch job to runtime-image or source-commit evidence, only when explicitly requested | [Trace a Batch job to source-commit evidence](references/batch.md) |

## Report evidence

- State the selected environment. For each operation, include applicable UTC
  bounds, result limit, truncation, and missing access.
- For results spanning imports, start with a compact table.
- Follow the evidence boundaries in
  [import evidence flow](references/import-evidence-flow.md).
  Do not synthesize an overall status from separate evidence sources.
- Include `Infrastructure actually used` for every cloud-backed answer,
  identifying queried and unresolved resources.
- Cite the repository files, cloud resources, logs, and GCS objects used. State
  the exact identifier used for cross-system correlation; otherwise report
  `ambiguous` or `unknown`.
