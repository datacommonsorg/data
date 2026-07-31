# Read one import record type from Spanner

Recipe ID: `gcp.spanner.read-import-records`

## Use when

Current publication state, accepted/version events, or downstream ingestion
history is specifically required.

## Required inputs

Verified Spanner project, instance, database, exact simple import name, one
query type, and row limit.

## Clarify when

Coordinates cannot be derived from the selected live helper deployment.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/import_support/read_import_records.py \
  --project=<PROJECT> \
  --instance=<INSTANCE> \
  --database=<DATABASE> \
  --import_name=<IMPORT_NAME> \
  --query=<current|version_history|ingestion_history> \
  --limit=<LIMIT>
```

## Preferred invocation

Choose exactly one query type. The focused helper exists because installed
`gcloud spanner databases execute-sql` has no bound-parameter flag. It executes
one parameterized `SELECT`, disables client metrics, and makes no schema or
follow-up queries.

## Expected output

Canonical database resource, selected query type, bounded rows, and truncation.

## Required bounds

Use exact coordinates/import name and a limit from 1 through 100. Never query
all three record types speculatively.

## Evidence to retain

Canonical database resource, query role, relevant row timestamps and status or
workflow fields, limit, and truncation.

## Common failures

Missing Application Default Credentials, schema drift, permission denied,
absent current row, or history that legitimately omits failed attempts.

## Related repository sources

A supplied sibling `ingestion-helper/clients/schema.sql`, live database
metadata, and the run/status reference.
