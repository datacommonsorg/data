# Deleted observation debugging

Use this guide to debug deleted observations or when a `FAILED` validation rule maps to `DELETED_RECORDS_COUNT` or `DELETED_RECORDS_PERCENT`. The failed rule confirms that deletions exceeded the configured threshold; it does not identify the cause.

## Hypothesis index

- [Source acquisition was incomplete](#source-acquisition-was-incomplete)
- [Retained source no longer contains the data](#retained-source-no-longer-contains-the-data)
- [Processing or mapping changed the observations](#processing-or-mapping-changed-the-observations)

## Understand what was deleted

Use these as possible investigations. Choose checks based on the observed
pattern and artifact sizes.

- Find the exact candidate's files with
  [List artifacts for one import version](../references/gcs.md#list-artifacts-for-one-import-version).
  The [artifact layout](../../../common/references/import-automation/artifact-layout.md)
  shows where validation and generated files are stored.
- Read `differ_summary.json` for overall counts and the current and previous
  inputs. Read `validation_output.csv` for the failed rule, threshold, and
  reported deletion count or percentage.
- Use `nodes-deleted.mcf` to inspect the previous-version representation of
  deleted nodes. It may be large and can contain non-observation nodes, so
  check its size and filter `StatVarObservation` nodes when appropriate.
- Useful deletion views include counts by `variableMeasured`,
  `observationAbout`, StatVar-place, `observationDate`, or observation facet.
  These are examples rather than a required checklist.
- For manageable MCF files, download to a system temporary directory and
  convert them to CSV with
  [mcf_file_util.py](../../../../tools/statvar_importer/mcf_file_util.py).
  Query the CSV with the DuckDB CLI when available, or repository Python with
  DuckDB otherwise. The converter loads each MCF into memory, so prefer another
  approach for files above roughly 2 GB.
- Compare the candidate and previous `summary_report.csv` files for missing
  StatVars or changes in observation, place, date, date-range, and facet
  counts. Use the previous input recorded in `differ_summary.json`.
- For StatVar Processor imports, use `manifest.json` to identify generated
  `cleaned_csv` files. Treat them as the source datasets when comparing the
  candidate and previous version. They may be large, so choose local querying
  or the short-lived BigQuery table based on their size. Use the processor
  command and `source_files` to identify the raw inputs and mappings.
- To load large GCS CSV, Parquet, or Avro files into a short-lived BigQuery
  table, read or run
  [create_short_lived_bq_table.sh](../scripts/create_short_lived_bq_table.sh)
  with `--help`. Give the user the exact command and ask them to return the full
  table name. Never run the table-creating command or delete a table.

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
