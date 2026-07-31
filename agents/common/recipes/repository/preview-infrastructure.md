# Preview import infrastructure

Recipe ID: `repository.preview-infrastructure`

## Use when

A request needs live Scheduler, Workflow, Batch, GCS, Cloud Run, Cloud Build,
Logging, or Spanner evidence.

## Required inputs

Request mode, exact import name for single-import inspection, selected
environment, UTC window, result limits, and any explicit infrastructure values
from the user.

## Clarify when

Two explicit sources disagree or the preview reports required Scheduler
coordinates unresolved.

## Read-only operation

Run the snapshot collector locally with the same arguments intended for cloud
collection and add `--preview_infrastructure`:

```bash
./agents/common/run_python.sh \
  agents/common/import_support/collect_import_snapshot.py \
  --mode=single_import \
  --import_name=<IMPORT_NAME> \
  --start_time=<RFC3339_UTC> \
  --end_time=<RFC3339_UTC> \
  --run_limit=<LIMIT> \
  --preview_infrastructure
```

Pass project, location, bucket, helper, or Spanner flags only when the user
explicitly supplies them or selects a supported non-production environment.

## Preferred invocation

Use this operation before the first cloud call. Print the returned candidates
and sources. Ask once in an interactive session; in a prompt-declared headless
run print `review: skipped (headless)` and continue only when
`ready_for_cloud` is true.

## Expected output

JSON on stdout containing `cloud_access_performed: false`, environment, query
bounds, selected and repository-candidate resources, source labels,
`ready_for_cloud`, unresolved values, blocked reads, and warnings.

## Required bounds

Use the same UTC window and hard result limits intended for collection. Do not
replace exact user values with broader projects, locations, or time ranges.

## Evidence to retain

Every selected value, its source, any replaced repository candidate, unresolved
fields, blocked reads, and the fact that no cloud access occurred.

## Common failures

Missing data-repository environment, invalid bounds, unresolved non-production
Scheduler coordinates, incomplete Spanner coordinates, or conflicting explicit
user sources.

## Related repository sources

`import-automation/executor/app/configs.py`, the snapshot collector, and the
shared environment-resolution reference.
