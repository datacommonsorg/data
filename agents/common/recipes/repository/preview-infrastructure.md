# Preview import infrastructure

Recipe ID: `repository.preview-infrastructure`

## Use when

A request needs live GCP evidence.

## Required inputs

Selected environment, planned recipes, exact import identity when applicable,
UTC window, limits, and any explicit user-provided infrastructure values.

## Clarify when

The environment is unknown, a required field remains unresolved, or two
explicit prompt values disagree.

## Read-only operation

Read the runtime environment file:

```bash
sed -n '1,200p' agents/common/config/import-environments.yaml
```

Select `prod` by default or the environment requested by the user, then apply
explicit prompt overrides field by field. Read an exact user-provided file only
when the user supplies its path; do not execute it. Print a review table with
these columns:

```text
operation | resource type | effective value | source | UTC bounds | limit
```

Use `environment_config` and `prompt_override` as coordinate sources. Include
only resources required by the planned recipes. Mark run-specific values such
as Workflow execution, Batch job, and GCS version as `runtime_identifier` to be
obtained by the selected bounded recipe.

## Preferred invocation

Use the environment file and review table above. Do not inspect deployment
source or call a collector or cloud API during preview. Ask once in an
interactive session. In a prompt-declared headless run, print
`review: skipped (headless)` after the table.

## Expected output

Selected environment, planned operations, effective resources with source
labels, unresolved fields, UTC bounds, limits, and whether review was approved
or skipped.

## Required bounds

Do not include services not required by the evidence plan. Do not replace exact
user values with broader projects, locations, buckets, or time ranges.

## Evidence to retain

Every proposed value and source, unresolved values, blocked operations, and the
fact that no cloud access occurred during preview.

## Common failures

Missing environment file or environment, incomplete coordinates, conflicting
explicit values, or a planned operation with no bounded recipe.

## Related repository sources

The [runtime environment file](../../config/import-environments.yaml) and the
shared environment-resolution reference.
