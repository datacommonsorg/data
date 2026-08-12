# Import automation architecture

## Scope and ET boundary

This reference describes extraction and transformation (ET): read source data,
transform and validate it, and produce Data Commons-compatible artifacts.
Loading an eligible artifact into the serving system is a separate pipeline.

One logical import is one selected specification in a repository
`manifest.json`. Its repository-relative manifest directory plus `import_name`
form the absolute import identity. The manifest defines repository intent;
editing it does not prove that a schedule or runtime deployment changed.

## Core lifecycle

- An **ET attempt** is one invocation of the shared ET Workflow. It can stop
  before producing a complete version.
- A **candidate ET version** is one version directory plus its exact
  `import_summary.json`, produced when an attempt reaches finalization.
- A **current ET output** (also called an accepted or promoted ET output) is an
  eligible candidate selected as the import's current ET result.
- **Eligible for downstream loading** means ET produced and accepted usable
  output. It does not mean the loader ran or serving data changed.

```text
ET attempt
  -> finalized candidate
       STAGING    -> eligible for acceptance -> current ET output
                                              -> eligible for downstream loading
       VALIDATION -> validation failed; current output unchanged
       SKIP       -> no meaningful change; current output unchanged

technical failure -> may stop before a version or summary exists
separate loader pipeline consumes eligible output (out of scope)
```

Acceptance is automatic ET behavior, not human approval. A `STAGING` summary
shows that a candidate is eligible; the current-output pointer proves which
eligible version is current at read time.

Successful Batch completion proves only the technical compute outcome. It does
not by itself prove that a version was accepted as the current ET output.

## Definition-to-run flow

```text
1. Define the import in Git
   manifest.json contains one or more import specifications.
   <directory-from-repository-root>:<import_name> is the absolute import name.

   example manifest:
     scripts/census_county_business_patterns/manifest.json
   example absolute import name:
     scripts/census_county_business_patterns:CensusCountyBusinessPatterns

2. Deploy a configured schedule
   a separate scheduling operation reads cron_schedule from the manifest.
   for each scheduled import, it creates or updates a Cloud Scheduler job.

3. Trigger an ET attempt
   Scheduler, or an explicit invocation, supplies the absolute import name to
   the environment's shared import-automation Workflow.

4. Orchestrate compute
   one Workflow execution represents one logical ET attempt.
   on the Batch-backed path, the Workflow creates a Cloud Batch job and task.

5. Finalize and classify a candidate
   the executor reads the selected manifest and source data, then transforms
   and validates the output. If finalization is reached, it writes a version
   directory, import_summary.json, and staging_version.txt in GCS.
   the summary classifies the candidate as STAGING, VALIDATION, or SKIP.

6. Select the current ET output
   after successful Batch completion, the Workflow invokes the update helper.
   the helper checks the finalized summary. Only STAGING is eligible for
   acceptance; successful acceptance advances the current-output pointer,
   normally latest_version.txt. VALIDATION and SKIP leave it unchanged.
```

The Workflow is shared by an environment; there is not one Workflow definition
per import. A Scheduler job exists only for an import whose schedule has been
deployed.

## Evidence is created at different points

Runtime records do not form one complete ledger:

- Cloud Spanner `ImportStatus` is a mutable current snapshot. It can expose the
  current raw state, recorded version, and ET Batch job ID, including a current
  failure. It is not history, and some fields can be updated by the separate
  loader.
- GCS version directories and summaries preserve finalized candidates.
  `staging_version.txt` identifies the most recent finalized candidate;
  `latest_version.txt` normally identifies the current ET output.
- Batch records technical compute state for an exact known job ID.

Therefore, GCS history covers finalized versions, not all attempts. In
particular, a Batch failure before `import_summary.json` is written has no GCS
history entry. It may be visible only while represented by the current
`ImportStatus` snapshot and retained Batch resource. Do not interpret a missing
summary as proof that no attempt occurred. Read the
[import evidence flow](import-evidence-flow.md) for evidence-selection rules.

## Resource cardinality

```text
per environment:          one shared import-automation Workflow deployment
per scheduled import:     one Cloud Scheduler job
per ET attempt:           one Workflow execution
per Batch-backed attempt: normally one Batch job and task
per finalized candidate:  one GCS version directory and import_summary.json
per import:                one mutable ImportStatus snapshot when present
```

## Evidence chain

| Layer | What it proves |
|---|---|
| Manifest | Versioned import definition and configured schedule intent |
| Scheduler | Deployed trigger and Workflow target, not ET completion |
| Shared Workflow | Orchestration design and one execution per logical attempt |
| Cloud Spanner `ImportStatus` | Mutable current state with recorded ET linkage when present; not history |
| Batch job/task | Technical compute request, state, resources, and task outcome for an exact job ID |
| Structured Batch logs | Bounded stage-level executor evidence for an exact job |
| GCS version and summary | Finalized candidate identity, classification, recorded ET linkage, and metrics |
| Current-output pointer | Which finalized candidate is the current ET output at read time |

Join systems only through exact identifiers returned by the selected evidence;
linked operational references define the valid fields. Do not correlate by
similar names or timestamps, and do not list Workflow executions or Batch jobs
to discover a missing run.

## Sources of truth

- Use the repository manifest for versioned definition and configured schedule
  intent.
- Use the selected environment block plus explicit prompt overrides for cloud
  coordinates.
- Use live Scheduler, current Cloud Spanner `ImportStatus`, exact Batch
  resources, GCS, and structured logs for deployed or runtime facts.
- A supplied sibling `import` checkout can explain Workflow or helper behavior
  when that implementation detail is specifically needed. The deployed
  Workflow revision and live metadata remain runtime truth.
- Batch records the requested image URI. Historical source resolution is a
  separate debugging concern.

## Read details only when needed

- For current-status, finalized-version, and missing-evidence semantics, read
  the [import evidence flow](import-evidence-flow.md).
- For version directories, summaries, and pointer names, read
  [artifact layout](artifact-layout.md).
- For exact import-definition fields, read the
  [manifest reference](manifest.md).

| Implementation question | Read on demand |
|---|---|
| How is a manifest schedule turned into a Scheduler request? | `import-automation/executor/app/executor/scheduler_job_manager.py` and `cloud_scheduler.py` |
| How are ET Workflow arguments constructed? | `import-automation/executor/app/executor/cloud_batch.py` |
| How does the shared Workflow create Batch or invoke accepted-output handling? | Optional sibling `../import/pipeline/workflow/import-automation-workflow.yaml` |
| What happens inside the ET container? | `import-automation/executor/main.py` and `import-automation/executor/app/executor/import_executor.py` |
| How are versions, summaries, and pointers produced? | `import_executor.py` plus `artifact-layout.md` |

Read the sibling Workflow only for an internal orchestration question. It is not
required for repository lookup, Scheduler verification, current status, GCS
versions, or exact Batch inspection.

This flow describes the `CLOUD_BATCH` path. GKE, GAE, and Cloud Run have
different execution paths and must not be interpreted as Batch without
path-specific evidence.
