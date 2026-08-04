# Import automation architecture

## Scope and ET boundary

This reference describes the extract-and-transform path through the accepted ET
output: read source data, transform it, validate it, and produce Data
Commons-compatible artifacts. Loading that output into the serving system is a
separate pipeline. This document identifies the boundary but does not describe
loader internals.

One logical import is one selected object in a repository `manifest.json`. Its
`import_name`, repository-relative directory containing that manifest, inputs,
scripts, validation settings, resources, and optional `cron_schedule` define
repository intent. Editing the manifest does not by itself prove that
production was updated; deployment or scheduling is a separate event.

## Definition-to-run flow

```text
1. Define the import in Git
   manifest.json contains one or more import specifications
   full directory path from the repository root + import_name form the absolute import name
   format: <directory-from-repository-root>:<import_name> (omit /manifest.json)
   example manifest: scripts/census_county_business_patterns/manifest.json
   example absolute name: scripts/census_county_business_patterns:CensusCountyBusinessPatterns

2. Deploy the configured schedule
   a separate scheduling operation reads cron_schedule
   it creates or updates one Cloud Scheduler job for the scheduled import

3. Trigger an ET attempt
   the Scheduler event identifies the exact absolute import name
   it invokes the environment's shared import-automation-workflow

4. Orchestrate the attempt
   one Workflow execution represents one logical ET attempt
   if execution reaches compute creation, it starts a Cloud Batch job and task

5. Produce a candidate ET version
   the executor reads the selected definition and source data
   it transforms, generates, and validates Data Commons-compatible artifacts
   it writes artifacts under one GCS version directory
   if finalization is reached, it writes staging_version.txt and import_summary.json
   the summary classifies the candidate as STAGING, VALIDATION, or SKIP

6. Decide whether to accept the candidate version
   after Batch succeeds, the Workflow invokes the version-update helper
   the helper reads staging_version.txt and the candidate's exact summary
   STAGING updates latest_version.txt and adds a new ImportVersionHistory event
   VALIDATION or SKIP leaves latest_version.txt on the previously accepted version

accepted ET output
  - - separate handoff - -> loader pipeline (out of scope)
```

The Workflow is shared by the environment; there is not one Workflow definition
per import.

## ImportVersionHistory stages

`ImportVersionHistory` is an event history, not the mutable current-state
record. In the normal automated flow:

- ET acceptance adds a `STAGING` event for the accepted version, linked to the
  import Workflow execution through its comment.
- `VALIDATION`, `SKIP`, and failures do not add an ET-acceptance event.
- The separate loader can later add a `SUCCESS` event for the same version. That
  event is loader evidence and is outside this ET flow.

Operational overrides and rollbacks can also add `STAGING` events. Use the
event's status, comment, and Workflow execution ID together when identifying
its source.

## Resource cardinality

```text
per environment:       one shared import-automation-workflow deployment
per scheduled import:  one Cloud Scheduler job
per ET attempt:        one Workflow execution
per Batch-backed run:  normally one Batch job and task
per uploaded attempt:  one GCS version directory and import_summary.json
```

## Evidence chain

| Layer | What it proves |
|---|---|
| Manifest | Versioned import definition and configured schedule intent |
| Scheduler | Deployed trigger and target, not ET completion |
| Workflow execution | Logical ET attempt, exact argument, historical revision, state, timestamps, and returned Batch job ID when successful |
| Batch job/task | Actual compute request, requested image URI, resources, events, and task outcome |
| Structured logs | Stage-level executor evidence |
| GCS version and `import_summary.json` | Output identity, pipeline status, version, and metrics |
| Accepted pointer or version history | Whether that ET version became the accepted ET output |

Join only through recorded identifiers. Verify the absolute import name,
Workflow `result.jobId`, Batch import/job identity, and summary import/job
identity. Similar names or timestamps alone are not sufficient.

Scheduler delivery, Workflow success, Batch success, pipeline status, semantic
validation, and accepted-output status are distinct states. A Workflow and Batch
job can succeed while the summary reports `VALIDATION` or `SKIP`.

## Sources of truth

- Use the selected block in `agents/common/config/import-environments.yaml` plus
  explicit prompt overrides only for infrastructure fields needed by the query.
- Use the repository manifest for versioned intent.
- Use live read-only Scheduler, Workflow, Batch, GCS, and database metadata for
  deployed and runtime state. Report drift instead of following unexpected
  resources.
- For historical behavior, the exact deployed Workflow revision is runtime
  truth. A supplied sibling `import` checkout can explain Workflow/helper
  behavior but is not required for routine navigation and does not override live
  evidence.
- Batch records the requested image URI. Resolving that image to historical
  source is a separate debugging operation.

## Read code only when needed

| Implementation question | Read on demand |
|---|---|
| How is a manifest schedule turned into a Scheduler request? | `import-automation/executor/app/executor/scheduler_job_manager.py` and `cloud_scheduler.py` |
| How are ET Workflow arguments constructed? | `import-automation/executor/app/executor/cloud_batch.py` |
| How does the shared Workflow create Batch or record accepted output? | Optional sibling `../import/pipeline/workflow/import-automation-workflow.yaml` |
| What happens inside the ET container? | `import-automation/executor/main.py` and `import-automation/executor/app/executor/import_executor.py` |
| How are versions, summaries, and pointers produced? | `import_executor.py` plus `artifact-layout.md` |

Read the sibling Workflow only for internal orchestration, argument mapping,
Batch construction, or accepted-output handoff behavior. Do not require it for
import lookup, deployed-schedule verification, run history, logs, or artifacts.

The evidence chain above describes the `CLOUD_BATCH` path. GKE, GAE, and Cloud
Run follow different execution paths and must not be interpreted as Batch
without path-specific evidence.
