# List repository-configured Data Commons imports

## Use when

One or more imports must be identified by a possibly incomplete, differently
cased, or misspelled manifest name, or filtered by configured cron intent,
without querying live infrastructure.

## Required inputs

- Optional `import_name` query.
- Auto-refresh filter: `any`, `configured`, or `not_configured`.
- Result limit from 1 through 100; use 5 for import selection.
- `data` repository as the working directory.

## Clarify when

Multiple prefix, substring, or fuzzy candidates remain plausible after using
the user's context. Execution time, operational status, and repeated failures
require cloud evidence.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/scripts/list_imports.py \
  --query='<IMPORT_NAME_QUERY>' \
  --autorefresh=<any|configured|not_configured> \
  --limit=<LIMIT>
```

## Preferred invocation

Use the command above with `--limit=5` for import selection. Do not replace it
with ad hoc manifest searches.

After selecting an import, read its exact manifest specification. Read the
[import manifest reference](../../../common/references/import-automation/manifest.md)
before interpreting manifest fields. Read manifest-referenced code only when
the request requires it.

The returned `gcs_object_prefix` is bucket-relative:

```text
<import_directory>/<import_name>
```

It contains no bucket or `gs://` scheme. For a cloud question, combine it later
with the effective environment as described by the
[import evidence flow](import-evidence-flow.md).

## Expected output

Deterministic JSON with the selected name-match strategy, applied filters,
bounded compact results, repository-relative manifest paths, absolute import
names, bucket-relative GCS object prefixes, scan/match/return counts, limit,
and truncation status. A unique exact or case-insensitive exact match may be
selected automatically. Use surrounding import context for weaker matches and
clarify when multiple candidates remain plausible.

## Required bounds

Scan only `statvar_imports/**/manifest.json` and
`scripts/**/manifest.json`; return at most 100 imports.

## Evidence to retain

Query, match strategy, manifest path, absolute import name,
`gcs_object_prefix`, cron schedule, configured-auto-refresh classification,
counts, limit, and truncation.

## Common failures

No credible match, ambiguous weak matches, duplicate import names, malformed
manifests, or an invalid result limit.

## Related repository sources

The [import manifest reference](../../../common/references/import-automation/manifest.md)
defines the selected-specification and field-interpretation contract. The
[import evidence flow](import-evidence-flow.md)
defines how repository identity seeds cloud evidence.
