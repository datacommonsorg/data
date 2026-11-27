# Canada Statistics (`CanadaStatistics`)

## Overview

This semi-automated import brings demographic, vital statistics, health, education, labour force, and agriculture statistics from **Statistics Canada** into Data Commons across national (`country/CAN`), provincial/territorial (`AdministrativeArea1`), and subnational municipal/city (`640` places total) geographies.

- **Source Portal**: [Statistics Canada](https://www150.statcan.gc.ca/n1/en/type/data?MM=1)
- **License**: [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada) (`ca-ogl-lgo`)
- **Import Type**: Semi-automated (weekly scheduled refresh from GCS-staged raw CSVs)
- **Why Semi-Automated**: `www150.statcan.gc.ca` (portal pages, WDS REST API, and `-eng.zip` bulk CSV endpoints) enforces a Cloudflare Managed Challenge (`HTTP 403`) that blocks automated cloud and CLI downloads. Raw CSVs are downloaded manually via a browser and staged in GCS (`gs://unresolved_mcf/country/canada/input_files/latest/`), then copied into `input_files/` by `run.sh` and processed directly by `stat_var_processor.py`.
- **Cron Schedule**: Weekly on Wednesday at `06:00 UTC` (`0 6 * * 3`) via `manifest.json`.

---

## Covered Datasets (8 Statistics Canada Cubes)

| # | Cube PID | Staged GCS Raw File (`latest/`) | Description | Frequency | Notes |
|---|---|---|---|---|---|
| 1 | `98-10-0001-01` | `Population.csv` | 2021 Census population and dwelling counts (`2016`, `2021`) | Quinquennial (`P5Y`) | Static until 2026 Census releases in 2027 |
| 2 | `32-10-0351-01` | `can_agri_producer_deliveries_major_grains.csv` | Producer deliveries of major grains (`1966-08`–present) | Monthly (`P1M`) | `unit=MetricTon`, `observationPeriod=P1M` |
| 3 | `13-10-0713-01` | `can_infant_mortality.csv` | Infant deaths and mortality rates by age group (`1991`–present) | Annual (`P1Y`) | `scalingFactor=1000` on rates; remapped via `config_files/can_sv_remap.csv` |
| 4 | `13-10-0837-01` | `can_life_expectancy.csv` | Complete life table single-year estimates (`1980`–present) | Annual (`P1Y`) | Skips non-`ex` life-table elements via `#IgnoreRow` so only life expectancy gets `unit=Year` |
| 5 | `13-10-0710-01` | `can_mortality_rate.csv` | Mortality rates (`1991`–present) and terminated death counts (`1991`–`2018`) by age & sex | Annual (`P1Y`) | Rates scaled via `#Multiply 0.001` (per-capita); remapped via `config_files/can_sv_remap.csv`; uses `[85 89 Years]` age range |
| 6 | `98-10-0127-01` | `can_pop_age_gender.csv` | 2021 Census population by age group, gender, and marital status (`2021`) | Quinquennial (`P5Y`) | Static until 2026 Census releases in 2027; uses `#Filter` to exclude national and provincial 15+ `Count_Person` totals that would otherwise collide with all-ages `Count_Person` from `98-10-0001-01` |
| 7 | `37-10-0007-01` | `can_public_school_enrollment.csv` | Public elementary and secondary school student enrollment by grade and sex (`1997/1998`–present) | Annual (`P1Y`) | Academic year `YYYY/YYYY` mapped to end year (`1998`–present); Ontario Grade 13 retired after `2012` |
| 8 | `14-10-0327-01` | `can_unemployment_rate_above15.csv` | Labour force characteristics by gender & age group, annual (`1976`–present) | Annual (`P1Y`) | Replaces archived `14-10-0334-01` and restores Ontario (`wikidataId/Q1904`); filters via `#IgnoreRow` to `Unemployment rate`, `Total - Gender`, `15 years and over` |

---

## Manual Data Acquisition & GCS Staging

When Statistics Canada publishes a new release for any active table (verifiable via Open Canada CKAN `https://open.canada.ca/data/api/3/action/package_show`):

1. Open the table page in a standard desktop browser and download the full CSV ZIP (**Download options → Download entire table (CSV)**):
   - `32-10-0351-01`: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3210035101` (`32100351-eng.zip`)
   - `37-10-0007-01`: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3710000701` (`37100007-eng.zip`)
   - `13-10-0713-01`: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310071301` (`13100713-eng.zip`)
   - `13-10-0837-01`: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310083701` (`13100837-eng.zip`)
   - `13-10-0710-01`: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310071001` (`13100710-eng.zip`)
   - `14-10-0327-01`: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410032701` (`14100327-eng.zip`)
   - `98-10-0001-01` & `98-10-0127-01`: Keep static 2021 Census CSVs pinned until 2026 Census releases start in 2027.
2. Unzip `<pid>-eng.zip` and rename `<pid>.csv` to the corresponding filename in the table above.
3. Upload the unchanged raw CSV(s) to GCS:
   ```bash
   gcloud storage cp <local_csv> gs://unresolved_mcf/country/canada/input_files/latest/
   ```

---

## Processing Details

All commands below assume the working directory is `statvar_imports/canada_statistics/` with the repo Python environment active (`source ../../.env/bin/activate`, created via `./run_tests.sh -r` from repo root).

1. **Fetch raw CSVs unchanged from GCS (`run.sh`)**:
   ```bash
   ./run.sh gs://unresolved_mcf/country/canada/input_files/latest/
   ```
   Clears stale local CSVs, copies all 8 raw CSVs into `input_files/` untouched, and verifies every required file is present so each version archives its exact raw source files under `<version>/source_files/input_files/`.

2. **Run StatVar Processor (`stat_var_processor.py`)**:
   Each of the 8 raw CSVs in `input_files/` is processed directly into its own `output/<dataset>.csv`, `output/<dataset>.tmcf`, and optional `output/<dataset>_stat_vars.mcf`:
   - `--pv_map=GEO:config_files/can_places_pvmap.csv,config_files/<dataset>_pvmap.csv`
   - `--config_file=config_files/common_metadata.csv`
   - `--input_columns=<N>` *(trims trailing unused StatCan metadata columns)*
   - `--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`
   - `--output_path=output/<dataset>`
   - `--output_counters=counters/<dataset>_counters.csv`
   - `--statvar_dcid_remap_csv=config_files/can_sv_remap.csv` *(for `can_infant_mortality` and `can_mortality_rate`)*

   All filtering (`#IgnoreRow` on non-place regions, non-`ex` life-table elements, and non-target LFS dimensions; `#Filter` on the 14 national and provincial 15+ `Count_Person` cells in `can_pop_age_gender`) is handled declaratively in the PV maps with no custom Python preprocessing script.

---

## Important Files

- `manifest.json`: Semi-automated import specification (`run.sh` + 8 `stat_var_processor.py` commands, unified `import_inputs` using common template `output/can_population.tmcf` across `output/*.csv` and `output/*.mcf`, `source_files`, `validation_config_file`, weekly `cron_schedule`, and `resource_limits`).
- `run.sh`: Copies raw staged CSVs from GCS into `input_files/` using `gcloud storage cp` and verifies all 8 expected files are present.
- `config_files/can_places_pvmap.csv`: Shared place DCID mapping loaded under the `GEO` namespace (Canada, 13 provinces/territories, `", place of residence"` variants, 640 subnational Census geos, and `#IgnoreRow` for unmapped/non-place statistical regions).
- `config_files/can_sv_remap.csv`: StatVar DCID remap (`Count_MortalityEvent_*` → `Count_Death_*`) for infant mortality and mortality rate tables.
- `config_files/common_metadata.csv`: Shared `stat_var_processor.py` configuration (`output_columns`, `header_rows=1`, `mapped_columns="2,4,5,6"`, `input_encoding=utf-8-sig`, `reconcile_nodes=False`).
- `config_files/can_*_pvmap.csv`: Per-table PV maps for all 8 datasets.
- `validation_config.json`: Three unified `SQL_VALIDATOR` rules (`check_max_date_consistent`, `check_max_date_freshness`, and `check_coverage_and_value_bounds`) enforcing per-cohort date consistency, cadence freshness, coverage, and value bounds across all 8 datasets.
- `test_data/`: Compact representative sample inputs and expected `.csv`/`.tmcf` outputs for PVMap verification.

---

## Testing & Verification

From `statvar_imports/canada_statistics/`, verify any PVMap against its `test_data/` fixture (pass the matching `--input_columns=<N>` from `manifest.json`):

```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/<dataset>_input.csv \
  --pv_map=GEO:config_files/can_places_pvmap.csv,config_files/<dataset>_pvmap.csv \
  --config_file=config_files/common_metadata.csv \
  --input_columns=<N> \
  --output_path=output_test/<dataset>_output \
  --output_counters=output_test/<dataset>_counters.csv
```
*(Append `--statvar_dcid_remap_csv=config_files/can_sv_remap.csv` for `can_infant_mortality` and `can_mortality_rate`.)*

From the repository root, run repo lint checks:

```bash
./run_tests.sh -l
```

---

## Refresh Procedure

1. Download updated CSV ZIP(s) in a browser from Statistics Canada, unzip, rename to the expected filename, and upload to `gs://unresolved_mcf/country/canada/input_files/latest/`.
2. Wait for the next scheduled Cloud Scheduler run (`0 6 * * 3`) or trigger the job manually.
3. Review `counters/*.csv`, `validation_config.json` results, and `import_differ` before approving publication.
