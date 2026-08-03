# Read one import record type from Spanner

Recipe ID: `gcp.spanner.read-import-records`

## Use when

Current publication state, accepted/version events, or downstream ingestion
history is specifically required.

## Required inputs

Spanner project, instance, and database from the effective environment; exact
simple import name; one query type; and row limit.

## Clarify when

A required effective coordinate is missing or explicit prompt values conflict.

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

The runtime environment file, live database metadata, and the run/status
reference. An optional sibling schema can explain implementation details.
