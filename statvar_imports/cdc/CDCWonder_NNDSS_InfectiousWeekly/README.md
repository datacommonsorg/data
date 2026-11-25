# CDCWonder_NNDSS_InfectiousWeekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER containing incident counts of infectious diseases reported by US states, New York City, the District of Columbia, US territories, and US Census divisions.

This `stat_var_processor` + `pvmap` pipeline uses the two-input (`history/` + `live`) architecture:
1. `download.py` syncs the frozen `2006–2021` historical archive (`cdc_nndss_weekly_tables_historical.csv` & `.tmcf`) from `gs://unresolved_mcf/cdc/nndss_infectious_diseasesweekly/history/` into `history/`, and downloads/preprocesses `2022+` data from the CDC Socrata SODA3 `x9gk-5huc` endpoint (`export.csv?accessType=DOWNLOAD`: comma-stripped `Current week` numeric values, `observationDate`, and complete-pair NY+NYC sum into `geoId/36`, retaining `measurementMethod: CDC_NNDSS_Diseases_WeeklyTables` for unbroken `2006–2026` time-series continuity with the historical archive) into `input_files/NNDSS_Weekly_Data.csv`.
2. `stat_var_processor.py` maps `2022+` observations to canonical StatVars via `nndss_weekly_pvmap.csv` into `output/nndss_weekly_output.{csv,tmcf}`.
3. `download.py --normalize_output` exposes `observationPeriod` as a column in `output/nndss_weekly_output.{csv,tmcf}` and `manifest.json` passes both `history/` and `output/` in a single `import_inputs` entry, so `genmcf`, differ, and validation evaluate both together (emitting `table_mcf_nodes_cdc_nndss_weekly_tables_historical.mcf` and `table_mcf_nodes_nndss_weekly_output.mcf`, served as `history/nodes.mcf@1` and `latest/nodes.mcf@1`).
4. **Post-2023 Case-Status Split Hepatitis Series**: Five post-2023 case-status split labels (`"Hepatitis A, Confirmed"`, `"Hepatitis B, acute, Confirmed"`, `"Hepatitis B, acute, Probable"`, `"Hepatitis B, perinatal, Confirmed"`, `"Hepatitis C, perinatal, Confirmed"`) are currently `#ignore`d in `nndss_weekly_pvmap.csv` (leaving the unsplit `ConditionHepatitisA_AcuteCondition`, `ConditionHepatitisB_AcuteCondition`, and perinatal Hepatitis B/C series ending in December 2023) until canonical `ConfirmedCase` / `ProbableCase` StatVars are added to `cdc_nndss_weekly.mcf` and synced to `stat_vars.mcf` prior to retiring `CDCWonder_NNDSS_Infectious_Weekly`.

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

## Using `test_data/`
Sample raw SODA3 source data (`test_data/sample_export.csv`), preprocessed input (`test_data/NNDSS_Weekly_Data.csv`), and expected output fixtures covering country (`country/USA`), US Census division (`usc/NewEnglandDivision`), state (`geoId/06`, `geoId/36`), territory (`geoId/72`), and city (`geoId/3651000`) place types are in `test_data/`:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv \
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

## Production Deployment & Refresh Procedure
- Weekly Cloud Batch refreshes run on schedule (`30 7 * * 4`) and evaluate both `history/` (`2006–2021`) and `output/` (`2022+`) in `import_inputs`.
- `validation_config.json` enforces `check_weekly_statvars_freshness` (`SQL_VALIDATOR`: `fresh_svs >= 50` within 30 days) and inherits the default `0.1%` `DELETED_RECORDS_PERCENT` threshold.
- **Two-Phase Production Deployment Steps**:
  1. Merge PR #2414 to `master` first so `dataTransformationLogic` resolves with `HTTP 200` and production Cloud Batch pulls the latest `statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/` scripts.
  2. Submit `cl/1023384799` to serve the verified `history/nodes.mcf@1` + `latest/nodes.mcf@1` snapshot (`631,362` observations).
  3. Trigger and manually approve the first production Cloud Batch run against the staged `20250206` baseline in `gs://datcom-prod-imports/statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/CDCWonder_NNDSS_InfectiousWeekly/` (`check_deleted_records_percent`: `0.1631%` = `877` deletions, `0` in `2006–2021` — `411` upstream CDC suppressions of `Hepatitis C, acute` in `2023–2024` across `Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_{ConfirmedCase,ConfirmedCase_NonUSResident,ProbableCase,ProbableCase_USResident}` + `466` intentional PVMAP `#ignore` removals of `20250206` mis-mappings: `463` `2022` `ConditionRabiesinhuman*` from `Rabies, Animal` and `3` `2023-04-09` `ConditionHaemophilusMeningitis*` from non-HPS `Hantavirus`), populating `datcom-prod-imports` with `<version>/nndss_weekly_output.{csv,tmcf}` and `import_metadata_mcf.mcf`.
  4. Submit the Phase-2 manifest CL wiring `download_config.src_latest_version_file` on the `latest/` `table`, `automated_mcf_generation_by`, `import_groups`, `metadata_mcf_url`, and `cachedSourceDataUrl` pointing to `datcom-prod-imports`.
  5. Before unscheduling or retiring `CDCWonder_NNDSS_Infectious_Weekly`, submit a schema CL adding canonical `ConfirmedCase` / `ProbableCase` StatVars for `HepatitisA__AcuteCondition`, `HepatitisB__AcuteCondition`, `HepatitisB__AcuteCondition__PerinatalInfection`, and `HepatitisC__AcuteCondition__PerinatalInfection` in `cdc_nndss_weekly.mcf`, sync `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`, and map the five post-2023 split Hepatitis labels in `nndss_weekly_pvmap.csv`.
