# Dynamic World V1 Flood Import (`DynamicWorld_Floods`)

## Overview
This import extracts monthly flood event area (`Area_FloodEvent`) and count (`Count_FloodEvent`) observations per S2 level-10 cell (`s2CellId/...`) directly from Google Earth Engine's Dynamic World V1 near-real-time land cover dataset:

- **Dataset Catalog**: [GOOGLE/DYNAMICWORLD/V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- **Earth Engine Collection ID**: `GOOGLE/DYNAMICWORLD/V1`
- **Land Mask Asset**: `UMD/hansen/global_forest_change_2025_v1_13` (`datamask == 1`)
- **Temporal Coverage**: Complete calendar months of the current year (YTD, `YYYY-MM`, period `P1M`)
- **Statistical Variables**: `Area_FloodEvent` (`SquareKilometer`), `Count_FloodEvent`
- **Refresh Schedule**: Monthly on the 2nd at 08:00 UTC (`0 8 2 * *`)

---

## Data Acquisition & Processing Architecture

1. **Direct Earth Engine Download & Raster-to-SVObs (`download_script.py`)**:
   - Queries `ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')` month-by-month over `[start_date, end_date)` (defaulting to YTD complete calendar months).
   - Classifies pixels where `water >= 0.7`, takes the monthly maximum, and masks out permanent water using `UMD/hansen/global_forest_change_2025_v1_13` (`datamask == 1`).
   - Splits bounding regions into 4°×4° tiles, requests signed GeoTIFF download URLs via `getDownloadURL()`, and downloads them directly into `input_files/geotiff/` via `util/download_util_script.download_file()` using atomic file writes (skipping tiles with empty Dynamic World imagery).
   - Converts GeoTIFF tiles into S2 Level-13 raster CSVs (`scripts/earthengine/raster_to_csv.py`) and monthly S2 Level-10 per-place FloodEvent SVObs (`scripts/earthengine/process_events.py`), publishing the consolidated CSV at `input_files/dynamic_world_flood_place_svobs.csv`.
2. **StatVar Processing (`tools/statvar_importer/stat_var_processor.py`)**:
   - Reads `input_files/dynamic_world_flood_place_svobs.csv` with `dynamic_world_flood_pvmap.csv`, `dynamic_world_flood_metadata.csv`, and `dynamic_world_flood_schema.mcf`.
   - Emits `output/dynamic_world_flood_output.csv`, `output/dynamic_world_flood_output.tmcf`, and processing counters `counters/dynamic_world_flood_counters.csv`.
3. **Lint, GenMCF, Differ & Validation**:
   - Validates and resolves MCF outputs with `import-tool.jar` (`lint` and `genmcf`).
   - Compares generated MCF against prior versions using `tools/import_differ/import_differ.py`.
   - Validates thresholds, date consistency/freshness, and golden sets against `validation_config.json` and `golden_data/`.

---

## Directory Structure

- `manifest.json`: Import automation specification, script sequence, `import_inputs`, retained `source_files`, and cron schedule (`0 8 2 * *`).
- `download_script.py`: Automated `absl` downloader querying Google Earth Engine directly and building consolidated place SVObs CSVs.
- `download_script_test.py`: Unit and end-to-end fixture parity tests.
- `dynamic_world_flood_pvmap.csv`: Property-value mappings for `Area_FloodEvent` and `Count_FloodEvent`.
- `dynamic_world_flood_metadata.csv`: `stat_var_processor.py` configuration (`header_rows=1`, `output_columns`).
- `dynamic_world_flood_schema.mcf`: StatisticalVariable definitions for `Area_FloodEvent` and `Count_FloodEvent`.
- `validation_config.json`: Import validation rules (`check_deleted_records_percent`, `check_max_date_consistent`, `check_flood_data_freshness`, `check_goldens_summary_report`, `check_goldens_output_csv`).
- `golden_data/`: Golden summary (`golden_summary_report.csv`) and observation property-set (`golden_observations.csv`) fixtures.
- `test_data/`: Hermetic sample input (`sample_place_svobs.csv`) and expected processor outputs (`expected_output.csv`, `expected_output.tmcf`).
- `requirements.txt`: Python dependencies for Earth Engine and raster/S2 processing.
- `run_pipeline.sh`: End-to-end local runner script.

---

## Manual Execution & Testing

Run from the repository root (`data/`):

```bash
# 1. Run unit & integration tests
./run_tests.sh -p statvar_imports/dynamic_world_flood

# 2. Run full local pipeline (download -> stat_var_processor -> lint -> genmcf -> optional differ)
bash statvar_imports/dynamic_world_flood/run_pipeline.sh

# 3. Custom date range / bounds / differ baseline:
START_DATE=2026-01-01 END_DATE=2026-11-01 BOUNDS=24.72,83.83,26.06,88.26 \
  PREV_OUTPUT_MCF=path/to/previous.mcf \
  bash statvar_imports/dynamic_world_flood/run_pipeline.sh
```
