# Import evidence flow

Use this reference when a runtime question requires current status, recent
versions, GCS evidence, or an exact Batch resource. It explains how to navigate
evidence; linked operation sections own the commands and bounds.

## Resolve the repository identity

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

## Resolve cloud coordinates only when needed

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

## Choose the evidence branch

| Requested fact | Starting evidence |
|---|---|
| Current status, current attempt, its recorded version, Batch ID, or timestamps | [Cloud Spanner `ImportStatus`](spanner.md) |
| Imports currently in a selected state and updated in a window | [Bounded `ImportStatus` query](spanner.md) |
| Recent versions that produced an import summary | [List recent import versions](gcs.md) |
| Classification or metrics for one version | [Exact `import_summary.json`](gcs.md) |
| Last successful or accepted version | [Find the last successful import version](gcs.md) |
| Technical state or logs | [Exact Batch job](batch.md) selected through an identifier returned by existing evidence |

Follow only an exact identifier returned by the selected evidence. Do not list
Workflow executions or Batch jobs to discover a missing run.

## Compare an import version with the last successful version

1. Use an exact version supplied or selected by the user. Otherwise, query the
   current `ImportStatus` and use the exact version recorded for the current
   attempt.
2. If the current attempt has no exact version, report that a version
   comparison is unavailable. For a diagnostic request, continue with its
   available runtime evidence instead of substituting another version.
3. Use [Find the last successful import version](gcs.md).
4. Read only the exact summaries or artifacts needed to compare the two
   versions, and label which evidence belongs to each version.

## Preserve evidence boundaries

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
