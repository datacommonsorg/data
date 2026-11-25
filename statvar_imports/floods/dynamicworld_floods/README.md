# Dynamic World V1 Flood Import (`DynamicWorld_Floods`)

## Overview
This import extracts monthly (`P1M`) flooded area observations (`Area_FloodEvent`, `SquareKilometer`, `measurementMethod: DataCommonsAggregate`) per S2 Level-13 cell (`s2CellId/...`) directly from Google Earth Engine's Dynamic World V1 near-real-time land cover dataset, preserving the production schema defined in `flood-svobs.tmcf`:

- **Dataset Catalog**: [GOOGLE/DYNAMICWORLD/V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- **Earth Engine Collection ID**: `GOOGLE/DYNAMICWORLD/V1`
- **Land Mask Asset**: `UMD/hansen/global_forest_change_2025_v1_13` (`datamask == 1`)
- **Temporal Coverage**: Complete calendar months YTD by default (`YYYY-01-01` through first day of current month; full prior calendar year in January), with automatic carry-forward of prior cached years across February year rollovers (`YYYY-MM`, period `P1M`)
- **Spatial Coverage**: Global (`-60,-180,75,180`) at S2 Level-13 cell granularity
- **Statistical Variable**: Canonical `Area_FloodEvent` (`SquareKilometer`, `measurementMethod: DataCommonsAggregate`), reused from `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`
- **Refresh Schedule**: Monthly on the 2nd at 08:00 UTC (`0 8 2 * *`)

---

## Earth Engine IAM & `--ee_project` Setup
`download_script.py` authenticates via Application Default Credentials (ADC) with scopes `earthengine` and `cloud-platform`. The GCP project used for Earth Engine requests is resolved in order:
1. `--ee_project` flag (if explicitly provided)
2. `GOOGLE_CLOUD_PROJECT` environment variable
3. ADC default quota/billing project
4. Fallback `datcom-import-automation-prod`

The executing user or Cloud Run service account must have Earth Engine API access (`roles/earthengine.viewer` and `roles/serviceusage.serviceUsageConsumer`) on the resolved project, plus read access to `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.

---

## Data Acquisition & Processing Architecture

1. **Direct Earth Engine Download, Monthly Raster Caching & S2 Consolidation (`download_script.py`)**:
   - Cleans stale local intermediate directories (`geotiff/`, `raster_csv/`, `events/`) on startup unless `--skip_existing=True` is passed.
   - Queries `ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')` month-by-month over `[start_date, end_date)` (defaulting to complete YTD calendar months).
   - Resolves each month's S2 Level-13 raster CSV (`dw_flood_YYYY-MM.csv`) in order: (1) local `input_files/raster_csv/` (when `--skip_existing=True`), (2) persistent executor-mounted cache `gcs_folder/raster_csv/` (`import_cache/DynamicWorld_Floods`, when `--use_gcs_cache=True` and global bounds), (3) object-only bootstrap from legacy production raster CSVs (`gs://datcom-prod-imports/scripts/floods/raster_csv/`), and (4) direct Google Earth Engine download (`water >= 0.7`, monthly `max()`, masked against `UMD/hansen/global_forest_change_2025_v1_13`, unmasked to `0`, skipping dry 4°×4° tiles) via parallel `getDownloadURL()` + `util/download_util_script.download_file()` (reusing per-thread `requests.Session` objects) and a single glob-based `scripts/earthengine/raster_to_csv.py` call (`dw_flood_<YYYY-MM-01>_*.tif`, avoiding `ARG_MAX` limits).
   - Persists full-YTD annual S2 SVObs CSVs to `gcs_folder/annual_svobs/` and carries forward prior automated years automatically across February year rollovers, publishing deterministic output at `input_files/dynamic_world_flood_s2_svobs.csv` (raising an error on conflicting duplicate keys).
2. **StatVar Processing (`tools/statvar_importer/stat_var_processor.py`)**:
   - Reads `input_files/dynamic_world_flood_s2_svobs.csv` with `dynamic_world_flood_pvmap.csv`, `dynamic_world_flood_metadata.csv`, and `--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` (reusing canonical `Area_FloodEvent` without emitting duplicate node MCFs; `import_inputs.node_mcf` is `"output/*.mcf"`).
   - Emits `output/dynamic_world_flood_output.csv`, `output/dynamic_world_flood_output.tmcf`, and processing counters `counters/dynamic_world_flood_counters.csv`.
3. **Validation (`validation_config.json`)**:
   - Configures import-specific `check_max_date_consistent` and month-level `check_flood_data_freshness` (`MaxDate` within 2 calendar months of `CURRENT_DATE`), merged with the global default validation rules (`check_deleted_records_percent` at `0.1%`, `check_empty_import`, `check_missing_refs_count`, `check_lint_error_count`).

---

## Consolidated CSV Schema

`input_files/dynamic_world_flood_s2_svobs.csv`:

| Column | Description | Example |
| --- | --- | --- |
| `observationAbout` | S2 Level-13 cell DCID | `dcid:s2CellId/0x5b267c8c00000000` |
| `observationDate` | Observation month (`YYYY-MM`) | `2026-10` |
| `observationPeriod` | ISO-8601 observation period | `P1M` |
| `area` | Flooded area in `SquareKilometer` (`Area_FloodEvent`) | `0.214031` |

---

## Historical Table Handling

In Google3 (`DynamicWorld_Floods.textproto`), historical observations for `2015-07` through `2022-10` (17,112,494 production S2 Level-13 observations) are preserved in a dedicated static historical `table` + `mcf_proto_url` block (`flood-svobs.tmcf` + `/cns/jv-d/home/datcom/v3_mcf/floods/dynamic_world/csv/*.csv`), while the automated `auto2w` Cloud Run table serves `2026+` observations via `src_latest_version_file`. Completed automated years (`2026`, `2027`, …) are cached under `gcs_folder/annual_svobs/` and carried forward automatically across February year rollovers so prior years are never deleted.

---

## Directory Structure

- `manifest.json`: Import automation specification, script sequence, `import_inputs` (`node_mcf: "output/*.mcf"`), retained `source_files`, resource limits, and cron schedule (`0 8 2 * *`).
- `download_script.py`: Automated `absl` downloader querying Google Earth Engine directly and building consolidated S2 Level-13 SVObs CSVs.
- `download_script_test.py`: Unit tests (auto-discovered via `__init__.py`).
- `dynamic_world_flood_pvmap.csv`: Property-value mappings for `Area_FloodEvent` (`SquareKilometer`, `measurementMethod: dcs:DataCommonsAggregate`).
- `dynamic_world_flood_metadata.csv`: `stat_var_processor.py` configuration (`header_rows=1`, `output_columns`, `output_precision_digits=6`, `reconcile_nodes=False`).
- `validation_config.json`: Import-specific validation rules (`check_max_date_consistent`, month-level `check_flood_data_freshness`), merged with the global defaults (`check_deleted_records_percent` at `0.1%`, `check_empty_import`, `check_missing_refs_count`, `check_lint_error_count`).
- `test_data/`: Hermetic sample input (`sample_s2_svobs.csv`) and expected processor outputs (`expected_output.csv`, `expected_output.tmcf`).
- `requirements.txt`: Python dependencies for Earth Engine, GCS, and raster/S2 processing.

---

## Manual Execution & Testing

Run from the repository root (`data/`):

```bash
# 1. Run unit tests (auto-discovered via __init__.py)
./run_tests.sh -u -p statvar_imports/floods/dynamicworld_floods

# 2. Download/refresh YTD globally (reusing cached monthly raster CSVs where available)
python3 statvar_imports/floods/dynamicworld_floods/download_script.py

# 3. Custom regional / single-month test run
python3 statvar_imports/floods/dynamicworld_floods/download_script.py \
  --start_date=2026-10-01 \
  --end_date=2026-11-01 \
  --bounds=24.72,83.83,26.06,88.26
```
