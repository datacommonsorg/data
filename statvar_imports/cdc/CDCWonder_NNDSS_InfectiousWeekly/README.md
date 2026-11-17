# CDCWonder_NNDSS_InfectiousWeekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER containing incident counts of infectious diseases reported by US states, New York City, the District of Columbia, US territories, and US Census divisions.

This `stat_var_processor` + `pvmap` pipeline:
1. Preprocesses `x9gk-5huc` (`Current week` numeric values, `observationDate`, NY+NYC sum) via `preprocess.py`.
2. Maps 2022–present observations to canonical StatVars via `stat_var_processor.py` and `nndss_weekly_pvmap.csv`.
3. Merges the 2006–2021 historical archive from `gs://unresolved_mcf/cdc/nndss_infectious_diseasesweekly/history/cdc_nndss_weekly_tables.csv` (stored locally under `history/`) via `merge_historical.py`.

## Prerequisites
- Run commands from `statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/`.
- Ensure Google Cloud Application Default Credentials (`gcloud auth application-default login`) are configured for `merge_historical.py` to download the `20250206` historical baseline from `gs://unresolved_mcf/` (or pass `--historical_local_path=<path>` for offline runs).

## Processing Instructions
```bash
cd statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly
python3 preprocess.py
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv \
  --config_file=nndss_weekly_metadata.csv \
  --statvar_dcid_remap_csv=statvar_dcid_remap.csv \
  --output_path=output/nndss_weekly_output \
  --output_counters=counters/nndss_weekly_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
python3 merge_historical.py
```

## Using `testdata/`
Sample preprocessed input and expected output fixtures are in `testdata/`:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=testdata/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv \
  --config_file=nndss_weekly_metadata.csv \
  --statvar_dcid_remap_csv=statvar_dcid_remap.csv \
  --output_path=testdata/nndss_weekly_output
```

## Running Unit Tests
Run from the repository root (matching CI `run_tests.sh -u`):
```bash
python3 -m unittest discover -v -s statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly -p '*_test.py'
```

## Refresh & Approval Procedure
- Weekly Cloud Batch refreshes run on schedule (`30 7 * * 4`) and preserve all `2006–2021` observations from `20250206` under `history/`.
- `validation_config.json` enforces `check_weekly_statvars_freshness` (`SQL_VALIDATOR`: `fresh_svs >= 50` within 30 days) and inherits the default `0.1%` `DELETED_RECORDS_PERCENT` threshold.
- On the first automated refresh against `20250206`, `check_deleted_records_percent` (`0.1631%` = `877` upstream `2022–2024` CDC revisions, `0` deletions in `2006–2021`) requires one-time manual approval.
