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

## ET lifecycle concepts

- An **ET attempt** is one invocation of the shared ET Workflow. It may stop
  before producing complete output.
- A **candidate ET version** is versioned output plus its exact summary after an
  attempt reaches finalization. Candidate means generated, not yet selected as
  the current ET output.
- **Acceptance** is the ET-only transition that selects an eligible candidate as
  the current ET output. It is not human approval and does not run the loader.
- The **current ET output**, also called the accepted ET output, is the selected
  version available for downstream selection. Being eligible downstream does
  not mean the loader ran or serving data changed.

```text
ET attempt
  -> finalized candidate ET version
       STAGING -> eligible for ET acceptance
          -> current ET output
          -> eligible for downstream selection
       VALIDATION -> not eligible; current output unchanged
       SKIP -> no new output to accept; current output unchanged

technical failure -> may stop before a complete candidate
separate loader pipeline consumes eligible output (out of scope)
```

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

5. Finalize and classify a candidate ET version
   the executor reads the selected definition and source data
   it transforms, generates, and validates Data Commons-compatible artifacts
   if finalization is reached, it writes one GCS version, staging_version.txt,
   and the candidate's exact import_summary.json
   the summary classifies the candidate as STAGING, VALIDATION, or SKIP

6. Apply ET acceptance
   after Batch succeeds, the Workflow invokes the version-update helper
   the helper reads staging_version.txt and the candidate's exact summary
   only STAGING is eligible for acceptance
   successful acceptance advances the configured current-output pointer
   (normally latest_version.txt) and records a corresponding ET version
   checkpoint in database metadata
   VALIDATION or SKIP leaves the previous current ET output unchanged

current ET output
  -> eligible for downstream selection
  -> separate loader pipeline (out of scope)
```

The Workflow is shared by the environment; there is not one Workflow definition
per import.

ET evidence is checkpointed progressively. Workflow history records attempts,
GCS records finalized candidates and the current-output pointer, and Spanner
version metadata such as `ImportVersionHistory` provides queryable version
checkpoints. Not every attempt reaches every checkpoint, and these records are
created separately. Treat partial or conflicting evidence as incomplete or
`unknown`; read the [run and status model](run-and-status-model.md) for lookup
and interpretation rules.

## Resource cardinality

```text
per environment:       one shared import-automation-workflow deployment
per scheduled import:  one Cloud Scheduler job
per ET attempt:        one Workflow execution
per Batch-backed run:  normally one Batch job and task
per finalized candidate: one GCS version directory and import_summary.json
```

## Evidence chain

| Layer | What it proves |
|---|---|
| Manifest | Versioned import definition and configured schedule intent |
| Scheduler | Deployed trigger and target, not ET completion |
| Workflow execution | Logical ET attempt, exact argument, historical revision, state, timestamps, and returned Batch job ID when successful |
| Batch job/task | Actual compute request, requested image URI, resources, events, and task outcome |
| Structured logs | Stage-level executor evidence |
| GCS version and `import_summary.json` | Finalized candidate identity, classification, version, and metrics |
| Current-output pointer (normally `latest_version.txt`) | Which version is the current ET output at read time |
| Spanner version metadata | Queryable version checkpoints and correlation identifiers, not complete attempt history |

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

## Conditional references

### Read detailed references only when needed

- For status dimensions, checkpoint semantics, and evidence lookup order, read
  the [run and status model](run-and-status-model.md).
- For version directories, summaries, and pointer names, read
  [artifact layout](artifact-layout.md).
- For exact import-definition fields, read the
  [manifest reference](manifest.md).

### Read code only when needed

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
