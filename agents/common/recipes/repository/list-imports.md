# List repository-configured Data Commons imports

Recipe ID: `repository.list-imports`

## Use when

Imports must be filtered by manifest name or configured cron intent without
querying live infrastructure.

## Required inputs

- Optional case-insensitive `import_name` substring.
- Auto-refresh filter: `any`, `configured`, or `not_configured`.
- Result limit from 1 through 100.
- `data` repository as the working directory.

## Clarify when

The user asks for execution time, operational status, or repeated failures;
those criteria require live fleet search.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/import_support/list_imports.py \
  --name_contains=<SUBSTRING> \
  --autorefresh=<any|configured|not_configured> \
  --limit=<LIMIT>
```

## Preferred invocation

Use the command above. Do not replace it with ad hoc manifest searches.

## Expected output

Deterministic JSON with mode, applied filters, bounded sorted results,
repository-relative manifest paths, scan/match/return counts, limit, and
truncation status. Render manifest paths as inline code so the complete value is
visible.

## Required bounds

Scan only `statvar_imports/**/manifest.json` and
`scripts/**/manifest.json`; return at most 100 imports.

## Evidence to retain

Manifest path, absolute import name, cron schedule, configured-auto-refresh
classification, counts, limit, and truncation.

## Common failures

Duplicate import names, malformed manifests, or an invalid result limit.

## Related repository sources

`agents/common/import_support/resolve_import.py` provides the shared manifest
catalog and canonical import records.
