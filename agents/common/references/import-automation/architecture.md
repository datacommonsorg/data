# Import automation architecture for support

This document provides the stable control-flow model used by support tools. It
does not define deployed project IDs, buckets, or resource names.

## Identity chain

```text
manifest import_name + manifest directory
  -> absolute import name: <directory>:<import_name>
  -> Cloud Scheduler job
  -> Scheduler HTTP target Workflow
  -> Workflow execution (one logical refresh run)
  -> Cloud Batch job and task
  -> structured Cloud Logging records
  -> GCS run directory and import_summary.json
  -> current publication and downstream-ingestion state
```

Never join resources only because their names share a substring. Verify every
available recorded identifier:

- Scheduler `description` and decoded request `argument.importName`.
- Workflow execution `argument.importName` and successful `result.jobId`.
- Batch runnable `IMPORT_NAME`, `BATCH_JOB_NAME`, and container arguments.
- GCS `import_summary.json` import and job identity.
- Spanner import name, version, job, and event comments.

## Canonical repository sources

- `statvar_imports/**/manifest.json` and `scripts/**/manifest.json`: import
  configuration, inputs, scripts, schedule, validation, and resources.
- `import-automation/executor/app/executor/scheduler_job_manager.py`: scheduler
  selection and request creation.
- `import-automation/executor/app/executor/cloud_scheduler.py`: Scheduler job
  ID, description, target, retry, and body shape.
- `import-automation/executor/app/executor/cloud_batch.py`: Scheduler Workflow
  argument shape.
- `import-automation/executor/main.py` and
  `import-automation/executor/app/executor/import_executor.py`: runtime config,
  stages, outputs, logs, and summary creation.
- `import-automation/executor/app/configs.py`: repository defaults and config
  field names. These are configured intent, not proof of live deployment.
- A supplied sibling `import` checkout can explain Workflow/helper behavior,
  but live Workflow revisions and live database metadata remain runtime truth.

## Source of truth

Use live read-only GCP state for what is deployed and running. Use repository
sources for versioned intent and interpretation. Use support documents only for
navigation and stable semantics. Record disagreements instead of applying a
silent precedence rule.

## Execution paths

The current recipes cover the `CLOUD_BATCH` path. The Scheduler code also
supports GKE, GAE, and Cloud Run. Recognize and report those target types as
unsupported for full V1 correlation rather than treating them as Batch.
