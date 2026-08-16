# Deleted observation debugging

Status: Placeholder. Do not use this file as an operational troubleshooting
procedure yet.

Use this guide when the user asks to debug deleted observations or a `FAILED`
validation rule maps to `DELETED_RECORDS_COUNT` or
`DELETED_RECORDS_PERCENT`. That failed row confirms that deleted observations
exceeded the configured threshold; it does not identify the root cause or prove
that a whole series was deleted.

## Questions to resolve

- Which persisted artifacts are required before diagnosis can begin?
- Which StatVar, place, StatVar-place, and series summaries should be derived?
- What evidence is sufficient to classify a whole-series deletion?
- How should delete-plus-add replacements be distinguished from true deletion?
- When should the investigation continue into source acquisition or processing?
- Which commands or helper scripts are reliable enough to include?

Until this guide is completed, report the confirmed threshold failure and use
the [Import Differ documentation](../../../../tools/import_differ/README.md) for
the current artifact and comparison contracts. Do not claim a deletion root
cause or whole-series deletion.
