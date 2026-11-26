# Dynamic World V1 Flood Events Places AutoRefresh (`DynamicWorld_FloodEvents_Places_AutoRefresh`)

## Overview
This import extracts monthly (`P1M`) and annual (`P1Y`) flood event area (`Area_FloodEvent`) and count (`Count_FloodEvent`) observations across S2 level-10 cells (`s2CellId/...`) and aggregated places (`Earth`, continents, `country/*`, `wikidataId/*`, `nuts/*`, `usc/*`, `geoId/*`, `zip/*`) directly from Google Earth Engine's Dynamic World V1 near-real-time land cover dataset:

- **Dataset Catalog**: [GOOGLE/DYNAMICWORLD/V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- **Earth Engine Collection ID**: `GOOGLE/DYNAMICWORLD/V1`
- **Land Mask Asset**: `UMD/hansen/global_forest_change_2025_v1_13` (`datamask == 1`)
- **Temporal Coverage**: Complete calendar months YTD by default (`YYYY-01-01` through first day of current month; full prior calendar year in January), with automatic carry-forward of prior cached years across February year rollovers (`P1M` and `P1Y` rollups; configurable `--start_date` / `--end_date` for custom windows)
- **Spatial Coverage**: Global (`-60,-180,75,180`) with `place_properties_cache_with_s2_10.pkl` place rollups matching `scripts/floods/flood_events_pipeline_config.py`
- **Statistical Variables**: Canonical `Area_FloodEvent` (`SquareKilometer`) and `Count_FloodEvent` (reused from `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`)
- **Refresh Schedule**: Monthly on the 1st at 05:00 UTC (`0 5 1 * *`)

---

## Earth Engine IAM & `--ee_project` Setup
`download_script.py` authenticates via Application Default Credentials (ADC) with scopes `earthengine` and `cloud-platform`. The GCP project used for Earth Engine requests is resolved in order:
1. `--ee_project` flag (if explicitly provided)
2. `GOOGLE_CLOUD_PROJECT` environment variable
3. ADC default quota/billing project
4. Fallback `datcom-import-automation-prod`

The executing user or Cloud Run service account must have Earth Engine API access (`roles/earthengine.viewer` and `roles/serviceusage.serviceUsageConsumer`) on the resolved project, plus read access to `gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl` and `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.

---

## Data Acquisition & Processing Architecture

1. **Direct Earth Engine Download, Monthly Raster Caching & Pipeline Event Aggregation (`download_script.py`)**:
   - Cleans stale local intermediate directories (`geotiff/`, `raster_csv/`, `events/`) on startup unless `--skip_existing=True` is passed.
   - Defaults to all complete calendar months YTD (`default_ytd_date_range()`) so every monthly refresh preserves all prior months (`P1M`) and produces accurate cumulative annual rollups (`P1Y`) with zero unintended deletions.
   - Resolves each month's S2 Level-13 raster CSV (`dw_flood_YYYY-MM.csv`) in order: (1) local `input_files/raster_csv/` (when `--skip_existing=True`), (2) persistent executor-mounted cache `gcs_folder/raster_csv/` (`import_cache/DynamicWorld_FloodEvents_Places_AutoRefresh`, when `--use_gcs_cache=True` and global bounds), (3) object-only bootstrap from legacy production raster CSVs (`gs://datcom-prod-imports/scripts/floods/raster_csv/`), and (4) direct Google Earth Engine download (`ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')`, `water >= 0.7`, monthly `max()`, masked against `UMD/hansen/global_forest_change_2025_v1_13`, unmasked to `0`, skipping dry 4°×4° tiles) via parallel `getDownloadURL()` + `util/download_util_script.download_file()` (with per-thread `requests.Session` reuse) and `scripts/earthengine/raster_to_csv.py`. Newly generated monthly raster CSVs are written through to `gcs_folder/raster_csv/` so subsequent runs only download the newly completed month.
   - Runs `scripts/earthengine/process_events.py` across non-empty YTD monthly raster CSVs per year with the settings from `scripts/floods/flood_events_pipeline_config.py` (`s2_level=10`, `max_overlap_place_hop=2`, `max_event_interval_days=45`, `output_place_svobs_dates=['YYYY-MM-DD', 'YYYY-MM', 'YYYY']`, `aggregate_by_contained_in_place=True`).
   - Persists full-YTD annual `place_svobs` CSVs to `gcs_folder/place_svobs/` and carries forward prior completed years automatically across February year rollovers, consolidating deterministic output at `input_files/dynamicworld_floodevents_places_svobs.csv` (raising an error on conflicting duplicate keys).
2. **StatVar Processing (`tools/statvar_importer/stat_var_processor.py`)**:
   - Reads `input_files/dynamicworld_floodevents_places_svobs.csv` with `dynamicworld_floodevents_places_pvmap.csv`, `dynamicworld_floodevents_places_metadata.csv`, and `--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` (reusing canonical StatVar definitions without emitting duplicate node MCFs; `import_inputs.node_mcf` is `"output/*.mcf"`).
   - Emits `output/dynamicworld_floodevents_places_output.csv`, `output/dynamicworld_floodevents_places_output.tmcf`, and counters `counters/dynamicworld_floodevents_places_counters.csv`.
3. **Validation (`validation_config.json`)**:
   - Configures import-specific `check_max_date_consistent` and month-level `check_flood_data_freshness` (`MaxDate` within 2 calendar months of `CURRENT_DATE`), merged with the global default validation rules (`check_deleted_records_percent` at `0.1%`, `check_empty_import`, `check_missing_refs_count`, `check_lint_error_count`).

---

## Consolidated CSV Schema

`input_files/dynamicworld_floodevents_places_svobs.csv`:

| Column | Description | Example |
| --- | --- | --- |
| `observationAbout` | Place or S2 Level-10 cell DCID | `country/IND`, `s2CellId/0x39ed540000000000` |
| `observationDate` | Month (`YYYY-MM`) or Year (`YYYY`) | `2026-10`, `2026` |
| `observationPeriod` | ISO-8601 observation period | `P1M`, `P1Y` |
| `area` | Flooded area in `SquareKilometer` (`Area_FloodEvent`) | `142.35` |
| `count` | Number of flood events (`Count_FloodEvent`) | `3` |

---

## Historical Table Handling

In Google3 (`DynamicWorld_FloodEvents_Places_AutoRefresh.textproto`), historical observations for `2015`–`2025` are preserved in a dedicated static historical `table` + `mcf_proto_url` block (`DynamicWorldFloods-events-2015`..`2025`), while the automated `auto2w` Cloud Run table serves `2026+` observations via `src_latest_version_file`. Completed automated years (`2026`, `2027`, …) are cached under `gcs_folder/place_svobs/` and carried forward automatically across February year rollovers so prior years are never deleted.

---

## Manual Execution & Testing

Run from the repository root (`data/`):

```bash
# 1. Run unit tests (auto-discovered via __init__.py)
./run_tests.sh -u -p statvar_imports/floods/dynamicworld_floodevents_places_autorefresh

# 2. Download/refresh YTD globally (reusing cached monthly raster CSVs where available)
python3 statvar_imports/floods/dynamicworld_floodevents_places_autorefresh/download_script.py

# 3. Custom regional / single-month test run
python3 statvar_imports/floods/dynamicworld_floodevents_places_autorefresh/download_script.py \
  --start_date=2026-10-01 \
  --end_date=2026-11-01 \
  --bounds=24.72,83.83,26.06,88.26
```
