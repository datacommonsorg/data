# Import evidence flow

Use this reference after the [architecture overview](architecture.md) when a
runtime question requires current status, finalized versions, GCS evidence, or
an exact Batch resource. It explains how to navigate evidence; linked operation
sections own the commands and bounds.

## 1. Resolve the repository identity

Use the [repository import-list reference](imports.md) and
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
| Current recorded state, version, Batch ID, or timestamps | [Cloud Spanner `ImportStatus`](spanner.md) |
| Imports currently in a selected state and updated in a window | [Bounded `ImportStatus` query](spanner.md) |
| Recent finalized versions | [GCS summary-list helper](gcs.md) |
| Classification or metrics for one version | [Exact `import_summary.json`](gcs.md) |
| Whether a version is the current ET output | [Exact current-output pointer](gcs.md) |
| Technical state or logs | [Exact Batch job](batch.md) selected through an identifier returned by existing evidence |

Follow only an exact identifier returned by the selected evidence. Do not list
Workflow executions or Batch jobs to discover a missing run.

## 4. Preserve evidence boundaries

`ImportStatus` is a Cloud Spanner table containing one mutable current row per
recorded import. It is the best starting point for current status, including a
current failure that produced no GCS summary, but it is not complete attempt
history. The linked operation section owns its supported fields, query forms,
exclusions, and bounds.

GCS summaries represent finalized candidates, while Batch represents technical
state for one exact selected job. These sources answer different questions and
none establishes facts owned by another source.

Read the architecture overview for candidate classification, partial evidence,
acceptance, and eligibility for downstream loading. Read each linked operation
section for the exact fields and operational behavior of its evidence source.
