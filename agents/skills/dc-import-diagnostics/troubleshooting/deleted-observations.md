# Deleted observation debugging

Use this guide to debug deleted observations or when a `FAILED` validation rule maps to `DELETED_RECORDS_COUNT` or `DELETED_RECORDS_PERCENT`. The failed rule confirms that deletions exceeded the configured threshold; it does not identify the cause.

## Hypothesis index

- [Source acquisition was incomplete](#source-acquisition-was-incomplete)
- [Retained source no longer contains the data](#retained-source-no-longer-contains-the-data)
- [StatVar Processor changed or dropped observations](#statvar-processor-changed-or-dropped-observations)
- [Other transformation code changed or dropped observations](#other-transformation-code-changed-or-dropped-observations)

## Understand what was deleted

Choose checks based on the deletion pattern and artifact sizes.

- Start with the exact candidate's
  [artifacts](../references/gcs.md#list-artifacts-for-one-import-version) and the
  [artifact layout](../../../common/references/import-automation/artifact-layout.md).
  Read `differ_summary.json` for overall counts and the exact current and
  previous inputs. Read `validation_output.csv` for the failed rule, threshold,
  and deletion count or percentage.
- Inspect `nodes-deleted.mcf` for deleted nodes from the previous version.
  It may be large and include non-observation nodes. Filter
  `StatVarObservation` nodes when needed.
- To find patterns in deleted observations, group by `variableMeasured`,
  `observationAbout`, StatVar-place, `observationDate`, or facet. These are
  examples; choose the views that fit the deletion pattern.
- Compare candidate and previous `summary_report.csv` files for missing
  StatVars or changes in observation, place, date, date-range, and facet
  counts. Use the previous input named in `differ_summary.json`.
- Use [Query import artifacts](../references/querying-artifacts.md) to choose
  local DuckDB, MCF-to-CSV conversion, or a user-created short-lived BigQuery
  table.

See [Import Differ](../../../../tools/import_differ/README.md) for artifact
semantics. It does not persist deletion summaries by StatVar, place, or
StatVar-place.

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

### StatVar Processor changed or dropped observations

- **Confirm or refute:** Compare the candidate and previous `cleaned_csv` files
  identified by `manifest.json`. These are the final tabular processor outputs
  supplied to `genmcf`, not raw source data. Compare retained counters for
  unusual changes in input, ignored, dropped, generated, or output rows. When
  `#input` is present, use it to trace representative observations to source
  context. Inspect the PV map and processor configuration for the affected
  rows. See the [StatVar Processor](../../../../tools/statvar_importer/README.md)
  for output and counter semantics.
- **Mitigate:** Correct the mapping, configuration, or processing condition. If
  the observation identity changed intentionally, report a replacement rather
  than a true deletion.

### Other transformation code changed or dropped observations

- **Confirm or refute:** When a complete final CSV is retained, compare the
  candidate and previous CSV directly. Otherwise compare the generated MCF
  under each version's `input<N>/genmcf/` directory. Trace representative
  deletions through the transformation code. Compare `nodes-added.mcf` when the
  change may be a delete-plus-add replacement.
- **Mitigate:** Correct the transformation or mapping. If the observation
  identity changed intentionally, report a replacement rather than a true
  deletion.

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
