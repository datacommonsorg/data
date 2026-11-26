# CDCWonder_NNDSS_InfectiousWeekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER containing incident counts of infectious diseases reported by US states, New York City, the District of Columbia, US territories, and US Census divisions.

This `stat_var_processor` + `pvmap` pipeline uses a two-input (`history/` + `live`) architecture:
1. `download.py` syncs the frozen `2006–2021` historical archive (`cdc_nndss_weekly_tables_historical.csv` & `.tmcf`) from `gs://unresolved_mcf/cdc/nndss_infectious_diseasesweekly/history/` into `history/`, and downloads/preprocesses `2022+` data from the CDC Socrata SODA3 `x9gk-5huc` endpoint (`export.csv?accessType=DOWNLOAD`) into `input_files/NNDSS_Weekly_Data.csv`. It strips thousands commas from `Current week`, computes `observationDate` from MMWR year/week, and computes complete-pair statewide `NEW YORK` (`geoId/36`) sums from `NEW YORK` (excluding NYC) + `NEW YORK CITY`, stamping derived `geoId/36` rows with `measurementMethod: dcAggregate/CDC_NNDSS_Diseases_WeeklyTables` and source-reported rows with `CDC_NNDSS_Diseases_WeeklyTables`.
2. `stat_var_processor.py` maps `2022+` observations to canonical StatVars via `nndss_weekly_pvmap.csv` and `nndss_weekly_places_pvmap.csv` into `output/nndss_weekly_output.{csv,tmcf}`, using `output_columns` in `nndss_weekly_metadata.csv` so `observationDate`, `observationPeriod`, and `measurementMethod` are always emitted as CSV columns matching the historical archive schema.
3. `manifest.json` passes both `history/` and `output/` in a single `import_inputs` entry so `genmcf`, differ, and validation evaluate the full `2006–present` series together.
4. **Mapped & Deferred Labels**: `Salmonella Typhi` and `Salmonella Paratyphi` labels are mapped to the curated `ConditionTyphoidFever` and `ConditionParatyphoid` StatVars. Five post-2023 case-status split Hepatitis labels (`"Hepatitis A, Confirmed"`, `"Hepatitis B, acute, Confirmed"`, `"Hepatitis B, acute, Probable"`, `"Hepatitis B, perinatal, Confirmed"`, `"Hepatitis C, perinatal, Confirmed"`) remain `#ignore`d in `nndss_weekly_pvmap.csv` (leaving the unsplit `ConditionHepatitisA_AcuteCondition`, `ConditionHepatitisB_AcuteCondition`, and perinatal Hepatitis B/C series ending in December 2023) until canonical `ConfirmedCase` / `ProbableCase` StatVars are reconciled in schema MCF and synced to `stat_vars.mcf`.

## Prerequisites
- Run commands from `statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/`.
- Ensure Google Cloud Application Default Credentials (`gcloud auth application-default login`) are configured for `download.py` to download `history/` from `gs://unresolved_mcf/` (or pass `--skip_gcs_history` for offline runs).

## Processing Instructions
```bash
cd statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly
python3 download.py
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv,nndss_weekly_places_pvmap.csv \
  --config_file=nndss_weekly_metadata.csv \
  --statvar_dcid_remap_csv=statvar_dcid_remap.csv \
  --output_path=output/nndss_weekly_output \
  --output_counters=counters/nndss_weekly_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## Using `test_data/`
Sample raw SODA3 source data (`test_data/sample_export.csv`), preprocessed input (`test_data/NNDSS_Weekly_Data.csv`), and expected output fixtures covering country (`country/USA`), US Census division (`usc/NewEnglandDivision`), state (`geoId/06`, `geoId/36`), territory (`geoId/72`), and city (`geoId/3651000`) place types, derived `geoId/36` `dcAggregate/` attribution, and Typhoid/Paratyphoid mappings are in `test_data/`:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv,nndss_weekly_places_pvmap.csv \
  --config_file=nndss_weekly_metadata.csv \
  --statvar_dcid_remap_csv=statvar_dcid_remap.csv \
  --output_path=test_data/nndss_weekly_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## Running Unit Tests
Run from the repository root (matching CI `run_tests.sh -u`):
```bash
python3 -m unittest discover -v -s statvar_imports/ -p 'download_test.py'
```

## Refresh & Validation
- Weekly automated refreshes run on schedule (`30 7 * * 4`, Thursday at 07:30 UTC) and evaluate both `history/` (`2006–2021`) and `output/` (`2022+`) in `import_inputs`.
- `validation_config.json` enforces `check_weekly_statvars_freshness` (`SQL_VALIDATOR`: `fresh_svs >= 50` within 30 days) and inherits the default `0.1%` `DELETED_RECORDS_PERCENT` threshold.
- Relative to the prior `20250206` manual snapshot, the initial automated refresh incurs a one-time `0.1631%` deletion diff (`877` observations, `0` in `2006–2021`: `411` upstream CDC suppressions of acute Hepatitis C in `2023–2024` and `466` intentional `#ignore` removals of prior `Rabies, Animal` and non-HPS `Hantavirus` mis-mappings), which requires one-time manual validation approval before subsequent weekly refreshes run automatically under the default `0.1%` threshold.
