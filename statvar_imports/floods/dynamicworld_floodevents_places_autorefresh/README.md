# Dynamic World V1 Flood Events Places AutoRefresh (`DynamicWorld_FloodEvents_Places_AutoRefresh`)

## Overview
This import extracts monthly (`P1M`) and annual (`P1Y`) flood event area (`Area_FloodEvent`) and count (`Count_FloodEvent`) observations across S2 level-10 cells (`s2CellId/...`) and aggregated places (`Earth`, continents, `country/*`, `wikidataId/*`, `nuts/*`, `usc/*`, `geoId/*`, `zip/*`) directly from Google Earth Engine's Dynamic World V1 near-real-time land cover dataset:

- **Dataset Catalog**: [GOOGLE/DYNAMICWORLD/V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- **Earth Engine Collection ID**: `GOOGLE/DYNAMICWORLD/V1`
- **Land Mask Asset**: `UMD/hansen/global_forest_change_2025_v1_13` (`datamask == 1`)
- **Temporal Coverage**: Complete calendar months YTD by default (`YYYY-01-01` through first day of current month; full prior calendar year in January), with automatic carry-forward of prior cached years across year rollovers (`P1M` and `P1Y` rollups; configurable `--start_date` / `--end_date` for custom windows)
- **Spatial Coverage**: Global (`-60,-180,75,180`) with `place_properties_cache_with_s2_10.pkl` place rollups matching `scripts/floods/flood_events_pipeline_config.py`
- **Statistical Variables**: `Area_FloodEvent` (`SquareKilometer`), `Count_FloodEvent`
- **Refresh Schedule**: Monthly on the 1st at 05:00 UTC (`0 5 1 * *`)

---

## Data Acquisition & Processing Architecture

1. **Direct Earth Engine Download, Monthly Raster Caching & Pipeline Event Aggregation (`download_script.py`)**:
   - Defaults to all complete calendar months YTD (`default_ytd_date_range()`) so every monthly refresh preserves all prior months (`P1M`) and produces accurate cumulative annual rollups (`P1Y`) with zero unintended deletions.
   - Resolves each month's S2 Level-13 raster CSV (`dw_flood_YYYY-MM.csv`) in order: (1) local `input_files/raster_csv/`, (2) persistent executor-mounted cache `gcs_folder/raster_csv/` (`import_cache/DynamicWorld_FloodEvents_Places_AutoRefresh`), (3) object-only bootstrap from legacy production raster CSVs (`gs://datcom-prod-imports/scripts/floods/raster_csv/`), and (4) direct Google Earth Engine download (`ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')`, `water >= 0.7`, monthly `max()`, masked against `UMD/hansen/global_forest_change_2025_v1_13`, unmasked to `0`, skipping dry 4°×4° tiles) via `getDownloadURL()` + `util/download_util_script.download_file()` and `scripts/earthengine/raster_to_csv.py`. Newly generated monthly raster CSVs are written through to `gcs_folder/raster_csv/` so subsequent runs only download the newly completed month.
   - Runs `scripts/earthengine/process_events.py` across all YTD monthly raster CSVs per year with the settings from `scripts/floods/flood_events_pipeline_config.py` (`s2_level=10`, `max_overlap_place_hop=2`, `max_event_interval_days=45`, `output_place_svobs_dates=['YYYY-MM-DD', 'YYYY-MM', 'YYYY']`, `aggregate_by_contained_in_place=True`).
   - Persists full-YTD annual `place_svobs` CSVs to `gcs_folder/place_svobs/` and carries forward prior years automatically across year rollovers, consolidating deterministic output at `input_files/dynamicworld_floodevents_places_svobs.csv`.
2. **StatVar Processing (`tools/statvar_importer/stat_var_processor.py`)**:
   - Reads `input_files/dynamicworld_floodevents_places_svobs.csv` with `dynamicworld_floodevents_places_pvmap.csv`, `dynamicworld_floodevents_places_metadata.csv`, and `dynamicworld_floodevents_places_schema.mcf`.
   - Emits `output/dynamicworld_floodevents_places_output.csv`, `output/dynamicworld_floodevents_places_output.tmcf`, and counters `counters/dynamicworld_floodevents_places_counters.csv`.
3. **Validation (`validation_config.json`)**:
   - Configures import-specific `check_max_date_consistent` and `check_flood_data_freshness`, merged with the global default validation rules (`check_deleted_records_percent`, `check_empty_import`, `check_missing_refs_count`, `check_lint_error_count`).

---

## Manual Execution & Testing

Run from the repository root (`data/`):

```bash
# 1. Run unit & integration tests
./run_tests.sh -p statvar_imports/floods/dynamicworld_floodevents_places_autorefresh

# 2. Download/refresh YTD globally (reusing cached monthly raster CSVs where available)
python3 statvar_imports/floods/dynamicworld_floodevents_places_autorefresh/download_script.py

# 3. Custom regional / single-month test run
python3 statvar_imports/floods/dynamicworld_floodevents_places_autorefresh/download_script.py \
  --start_date=2026-10-01 \
  --end_date=2026-11-01 \
  --bounds=24.72,83.83,26.06,88.26
```
