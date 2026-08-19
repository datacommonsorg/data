# Deleted observation debugging

Use this guide when the user asks to debug deleted observations or a `FAILED`
validation rule maps to `DELETED_RECORDS_COUNT` or
`DELETED_RECORDS_PERCENT`. The failed rule confirms that deletions exceeded
the configured threshold; it does not identify the cause.

## Hypothesis index

- [Source acquisition was incomplete](#source-acquisition-was-incomplete)
- [Retained source no longer contains the data](#retained-source-no-longer-contains-the-data)
- [Processing or mapping changed the observations](#processing-or-mapping-changed-the-observations)

## Triage

- Use the exact candidate's `differ_summary.json` and `nodes-deleted.mcf`.
- Start with representative StatVar-place groups instead of tracing every
  deleted point.
- Treat `nodes-deleted.mcf` as the previous-version representation of deleted
  points. It does not prove that a whole series was deleted.
- Test the strongest plausible hypothesis first.

For artifact and comparison semantics, use the
[Import Differ documentation](../../../../tools/import_differ/README.md).
Import Differ does not persist deletion summaries grouped by StatVar, place,
or StatVar-place.

## Hypotheses

### Source acquisition was incomplete

- **Confirm or refute:** Follow
  [Source acquisition completeness](source-acquisition.md).
- **Mitigate:** Address a confirmed acquisition failure before investigating
  downstream processing.

### Retained source no longer contains the data

- **Confirm or refute:** Map representative deleted observations back to the
  retained source. For StatVar Processor imports, use the PV map; for other
  imports, use the transformation code. Check whether the corresponding source
  rows still exist.
- **Mitigate:** Identify the source, endpoint, or query change when the rows are
  absent.

### Processing or mapping changed the observations

- **Confirm or refute:** When the source rows exist, check whether their current
  generated observations are missing or have a different observation identity.
  Use the PV map and StatVar Processor evidence for StatVar Processor imports;
  use the transformation code and its evidence for other imports. Compare
  `nodes-added.mcf` when the change may be a delete-plus-add replacement.
- **Mitigate:** Correct the mapping or processing issue. If the identity change
  is intentional, report a replacement instead of a true deletion.

## Classify the impact

- Use StatVar-place grouping for a compact impact view.
- Treat a series as StatVar, place, and observation facet. Dates are points
  within the series.
- Claim whole-series deletion only when the current generated data contains no
  point for the same facet-aware series.

## Report

- State the likely cause and strongest supporting evidence.
- Distinguish deleted points, whole-series deletion, and replacement.
- State unresolved gaps and the next useful check.
