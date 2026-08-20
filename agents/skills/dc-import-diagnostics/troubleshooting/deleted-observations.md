# Deleted observation debugging

Use this guide to debug deleted observations or when a `FAILED` validation rule maps to `DELETED_RECORDS_COUNT` or `DELETED_RECORDS_PERCENT`. The failed rule confirms that deletions exceeded the configured threshold; it does not identify the cause.

## Hypothesis index

- [Source acquisition was incomplete](#source-acquisition-was-incomplete)
- [Retained source no longer contains the data](#retained-source-no-longer-contains-the-data)
- [Processing or mapping changed the observations](#processing-or-mapping-changed-the-observations)

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
- For manageable MCF files, download to a system temporary directory, convert
  them with
  [mcf_file_util.py](../../../../tools/statvar_importer/mcf_file_util.py) and
  query the CSV with the DuckDB CLI or repository Python. The converter loads
  the MCF into memory, so avoid it for files above roughly 2 GB.
- Compare candidate and previous `summary_report.csv` files for missing
  StatVars or changes in observation, place, date, date-range, and facet
  counts. Use the previous input named in `differ_summary.json`.
- For StatVar Processor imports, compare the `cleaned_csv` files identified by
  `manifest.json` for the candidate and previous version. These are final
  tabular processor outputs that are converted to MCF, not source data. Query
  them directly instead of converting the corresponding MCF back to CSV.
  Choose local queries or the short-lived BigQuery table based on size. Use the
  processor command and `source_files` to trace raw inputs and mappings.
- For large GCS CSV, Parquet, or Avro files, consult
  [create_short_lived_bq_table.sh](../scripts/create_short_lived_bq_table.sh)
  with `--help`, then give the user the exact command and ask for the returned
  table name. Never run the table-creating command or delete a table.

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
