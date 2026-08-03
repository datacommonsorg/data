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
- `agents/common/config/import-environments.yaml`: support-tool coordinates for
  production and staging. Explicit request-scoped overrides take precedence.
- `import-automation/executor/app/configs.py`: executor defaults and config field
  names, not the support skill's environment lookup path.
- An optional sibling `import` checkout can explain Workflow/helper and loader
  implementation, but routine support does not require it for coordinates.

## Source of truth

Use the environment file plus explicit prompt overrides for query coordinates.
Use live read-only GCP state for what is deployed and running, not to discover
replacement coordinates. Use repository sources for versioned intent and
interpretation. Report scope disagreements instead of following unexpected
resources.

## Execution paths

The current recipes cover the `CLOUD_BATCH` path. The Scheduler code also
supports GKE, GAE, and Cloud Run. Recognize and report those target types as
unsupported for full V1 correlation rather than treating them as Batch.
