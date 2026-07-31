# Find a historical import summary

Recipe ID: `gcp.gcs.find-historical-summary`

## Use when

A selected older Workflow run needs semantic status and its exact version URI
was not recorded elsewhere.

## Required inputs

Verified GCS project, bucket, import prefix, expected import name, expected
Batch job ID, Workflow start time, and candidate limit.

## Clarify when

The Workflow run has no recorded Batch job ID or the time correlation is too
wide to produce date-scoped candidates.

## Read-only operation

Convert the Workflow start time to `America/Los_Angeles`, where executor version
names are generated. Search only that date and an adjacent date when the run is
near midnight:

```bash
gcloud storage objects list \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<YYYY_MM_DD>*/import_summary.json' \
  --project=<PROJECT> \
  --sort-by='~updateTime' \
  --limit=<CANDIDATE_LIMIT> \
  --format='json(name,bucket,size,updateTime,generation)'
```

Read candidate summaries one at a time with the exact-summary recipe and stop
at the first exact import-name and job-ID match.

## Preferred invocation

Use this only after exact pointers, Workflow results, and a matching current
Spanner row cannot provide the requested historical semantic status.

## Expected output

One exact matching summary, or an explicit missing, ambiguous, or truncated
result.

## Required bounds

Use one or two explicit date prefixes and a small candidate limit. Never use
a recursive all-version summary pattern or list all summaries.

## Evidence to retain

Date prefixes, candidate limit, object metadata inspected, exact matched URI,
identity checks, and truncation.

## Common failures

Technical failure before summary creation, timezone boundary, deleted history,
identity mismatch, ambiguous candidates, permission denied, or truncation.

## Related repository sources

Version creation and summary upload in
`import-automation/executor/app/executor/import_executor.py`.
