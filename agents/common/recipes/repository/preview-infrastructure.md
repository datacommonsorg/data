# Preview import infrastructure

Recipe ID: `repository.preview-infrastructure`

## Use when

A request needs live GCP evidence.

## Required inputs

Selected environment, planned recipes, exact import identity when applicable,
UTC window, limits, and any explicit user-provided infrastructure values.

## Clarify when

Required values remain unresolved, two explicit sources disagree, or a
non-production environment has no canonical repository deployment definition.

## Read-only operation

Read production candidates from their repository source rather than copying
them into the skill:

```bash
rg -n \
  'gcp_project_id:|gcs_project_id:|storage_prod_bucket_name:|scheduler_location:|cloud_workflow_id:' \
  import-automation/executor/app/configs.py
```

Read an exact user-provided file only when the user supplies its path. Do not
execute it. Then print a review table with these columns:

```text
operation | resource type | candidate value | source | UTC bounds | limit
```

Include only resources required by the planned recipes. Mark downstream values
such as Batch job, version, or Spanner database as `derive after selected live
read` instead of resolving them upfront.

## Preferred invocation

Use repository reads and the review table above. Do not call a collector or any
cloud API during preview. Ask once in an interactive session. In a
prompt-declared headless run, print `review: skipped (headless)` after the table.

## Expected output

Selected environment, planned operations, resource candidates with source
labels, unresolved fields, UTC bounds, limits, and whether review was approved
or skipped.

## Required bounds

Do not include services not required by the evidence plan. Do not replace exact
user values with broader projects, locations, buckets, or time ranges.

## Evidence to retain

Every proposed value and source, unresolved values, blocked operations, and the
fact that no cloud access occurred during preview.

## Common failures

Missing repository configuration, incomplete non-production coordinates,
conflicting explicit values, or a planned operation with no bounded recipe.

## Related repository sources

`import-automation/executor/app/configs.py`, deployment definitions under
`import-automation/`, and the shared environment-resolution reference.
