# Import evidence flow

Use this reference after the [architecture overview](architecture.md) when a
runtime question requires current status, finalized versions, GCS evidence, or
an exact Batch resource. It explains how to navigate evidence; linked recipes
own the commands and bounds.

## 1. Resolve the repository identity

Use the [local import-list recipe](../../recipes/local/list-imports.md) and
retain the selected `import_name`, `absolute_import_name`, `manifest_path`,
`import_directory`, `gcs_object_prefix`, and configured cron fields.

```text
import_name:
  CensusCountyBusinessPatterns

absolute_import_name:
  scripts/census_county_business_patterns:CensusCountyBusinessPatterns

gcs_object_prefix:
  scripts/census_county_business_patterns/CensusCountyBusinessPatterns
```

## 2. Resolve cloud coordinates only when needed

Follow [environment resolution](environment-resolution.md) to obtain the GCS
client project and output bucket, Spanner project/instance/database, and Batch
project/location used by the selected operation.

```text
gcs_import_base_uri =
  gs://<output_bucket>/<gcs_object_prefix>

gcs_version_uri =
  <gcs_import_base_uri>/<version>
```

`gcs_object_prefix` is bucket-relative and is not a complete GCS URI. Always
prepend the effective environment's output bucket. Do not interpret `scripts`
or `statvar_imports` as a bucket name.

Normally use the exact `gcs_version_uri` returned by the bounded summary-list
helper. Construct it only when an exact version was supplied separately.

## 3. Choose the evidence branch

| Requested fact | Starting evidence |
|---|---|
| Current recorded state, version, Batch ID, or timestamps | [Cloud Spanner `ImportStatus`](../../recipes/gcp/spanner/query-import-status.md) |
| Imports currently in a selected state and updated in a window | [Bounded `ImportStatus` query](../../recipes/gcp/spanner/query-import-status.md) |
| Up to five recent finalized versions | [GCS summary-list helper](../../recipes/gcp/gcs/list-import-summaries.md) |
| Classification or metrics for one version | [Exact `import_summary.json`](../../recipes/gcp/gcs/read-version-summary.md) |
| Whether a version is the current ET output | [Exact current-output pointer](../../recipes/gcp/gcs/read-version-pointer.md) |
| Technical state or logs | [Exact Batch job](../../recipes/gcp/batch/describe-job.md) from `ImportStatus.JobId` or a validated summary |

Follow only an exact identifier returned by the selected evidence. Do not list
Workflow executions or Batch jobs to discover a missing run.

## 4. Preserve evidence boundaries

`ImportStatus` is a Cloud Spanner table containing one mutable current row per
recorded import. It is the best starting point for current status, including a
current failure that produced no GCS summary, but it is not complete attempt
history. Its `JobId` is the ET Batch identifier. Its `WorkflowId` is
loader-owned, may describe an earlier loader run, and is not an ET Workflow
execution ID; never select or follow it.

GCS summary history contains only attempts that reached summary creation. A
pre-summary Batch failure is absent, so missing GCS summary evidence does not
mean no attempt occurred.

Keep `current_status`, `summary_status`, `is_current`, and `batch_state`
separate. Read the architecture overview for `STAGING`, `VALIDATION`, `SKIP`,
acceptance, and eligibility for downstream loading.
