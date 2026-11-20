# CDCWonder_NNDSS_InfectiousWeekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER containing incident counts of infectious diseases reported by US states, New York City, the District of Columbia, US territories, and US Census divisions.

This `stat_var_processor` + `pvmap` pipeline uses the two-input (`history/` + `live`) architecture:
1. `download.py` syncs the frozen `2006–2021` historical archive (`cdc_nndss_weekly_tables_historical.csv` & `.tmcf`) from `gs://unresolved_mcf/cdc/nndss_infectious_diseasesweekly/history/` into `history/`, and downloads/preprocesses `2022+` data from `x9gk-5huc` (`Current week` numeric values, `observationDate`, NY+NYC sum) into `input_files/NNDSS_Weekly_Data.csv`.
2. `stat_var_processor.py` maps `2022+` observations to canonical StatVars via `nndss_weekly_pvmap.csv` into `output/nndss_weekly_output.{csv,tmcf}`.
3. `download.py --normalize_output` exposes `observationPeriod` as a column in `output/nndss_weekly_output.{csv,tmcf}` and `manifest.json` passes both `history/` and `output/` in a single `import_inputs` entry, so `genmcf`, differ, and validation evaluate both together (emitting `nodes.mcf-00000-of-00002` and `nodes.mcf-00001-of-00002`).

## Prerequisites
- Run commands from `statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/`.
- Ensure Google Cloud Application Default Credentials (`gcloud auth application-default login`) are configured for `download.py` to download `history/` from `gs://unresolved_mcf/` (or pass `--skip_gcs_history` for offline runs).

## Processing Instructions
```bash
cd statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly
python3 download.py
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv \
  --config_file=nndss_weekly_metadata.csv \
  --statvar_dcid_remap_csv=statvar_dcid_remap.csv \
  --output_path=output/nndss_weekly_output \
  --output_counters=counters/nndss_weekly_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
python3 download.py --normalize_output
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
python3 -m unittest discover -v -s statvar_imports/ -p 'download_test.py'
```

## Refresh & Approval Procedure
- Weekly Cloud Batch refreshes run on schedule (`30 7 * * 4`) and evaluate both `history/` (`2006–2021`) and `output/` (`2022+`) in `import_inputs`.
- `validation_config.json` enforces `check_weekly_statvars_freshness` (`SQL_VALIDATOR`: `fresh_svs >= 50` within 30 days) and inherits the default `0.1%` `DELETED_RECORDS_PERCENT` threshold.
- On the first automated refresh against `20250206`, `check_deleted_records_percent` (`0.1631%` = `877` upstream `2022–2024` CDC revisions, `0` deletions in `2006–2021`) requires one-time manual approval.
