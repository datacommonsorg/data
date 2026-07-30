# Read import state and history from Spanner

Recipe ID: `gcp.spanner.read-import-records`

## Use when

Current publication state, accepted/version events, or downstream ingestion
history is required.

## Required inputs

Verified Spanner project, instance, database, exact simple import name, and
row limit.

## Clarify when

Coordinates cannot be derived from the selected live helper deployment.

## Read-only operation

Use the parameterized Spanner adapter in the snapshot collector. It executes
an `INFORMATION_SCHEMA.COLUMNS` check for the three named tables, then only
these bounded `SELECT` shapes when the expected columns are present:

```sql
SELECT <allowlisted current-state columns>
FROM ImportStatus WHERE ImportName = @import_name;
SELECT <allowlisted version-event columns>
FROM ImportVersionHistory WHERE ImportName = @import_name
ORDER BY UpdateTimestamp DESC LIMIT @limit;
SELECT <allowlisted downstream-ingestion columns>
FROM IngestionHistory
WHERE @import_name IN UNNEST(IngestedImports)
ORDER BY CreationTimestamp DESC LIMIT @limit;
```

## Preferred invocation

Use the Python adapter because the installed `gcloud spanner databases
execute-sql` command does not support bound parameters.

## Expected output

One current row, bounded version events, and bounded downstream ingestion
events, each labeled by role.

## Required bounds

Exact import parameter and explicit row limit. Reject non-`SELECT` SQL.

## Evidence to retain

Database resource, query role, row timestamps, version/status/workflow fields,
and truncation.

## Common failures

Missing ADC, schema drift, permission denied, absent current row, or history
that legitimately omits failed attempts.

## Related repository sources

A supplied sibling `ingestion-helper/clients/schema.sql` and live database
metadata.
