### CDC WONDER County-Level Mortality Across All Causes (`CDC_Mortality_UnderlyingCause_County`)

This import acquires and processes county-level mortality statistics across all causes of death (ICD-10 113 Cause List) for all 50 US States and Washington D.C. from the CDC WONDER database.

- **Import Name**: `CDC_Mortality_UnderlyingCause_County`
- **Source Databases**:
  - **1999–2017 (Static Historical)**: Pre-downloaded from CDC WONDER Database `D76` and stored in GCS at `gs://unresolved_mcf/cdc/UnderlyingCause/county_mortality_underlyingCause/input_files/UnderlyingCauseofDeath_County_1999_2017.csv`
  - **2018–Present (Live)**: CDC WONDER Underlying Cause of Death (Database `D158`: `https://wonder.cdc.gov/ucd-icd10-expanded.html`)
- **Geographic Granularity**: County level (all ~3,147 US counties across all states)
- **Temporal Coverage**: 1999 to 2024 (P1Y frequency)
- **Cause Coverage**: All diseases in the ICD-10 113 Cause List (123 unique StatVars across 1999–2024, e.g. Septicemia, Diabetes Mellitus, Major Cardiovascular Diseases, Alzheimer's, Malignant Neoplasms, Respiratory Diseases, etc.)

---

### Workflow

The import consists of two fully automated steps:

#### Step 1: Download Source Data
```bash
python3 download.py
```
or with specific flags:
```bash
python3 download.py --states=all --years=2018-2024 --output_dir=input_files
```
The download script copies the static `1999–2017` historical CSV from `gs://unresolved_mcf/cdc/UnderlyingCause/county_mortality_underlyingCause/input_files` into `input_files/` and then downloads `2018–present` data live from CDC WONDER (Database `D158`), automatically handling sessions, agreements, rate-limiting backoffs, and query partitioning.

#### Step 2: Process Data into Cleaned SVObs and TMCF
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/*.csv \
  --pv_map=county_mortality_pvmap.csv \
  --config_file=county_mortality_metadata.csv \
  --output_path=output/underlyingcauseofdeath_county \
  --output_counters=counters/underlyingcauseofdeath_county_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

#### Output Artifacts
* `output/underlyingcauseofdeath_county.csv`: Cleaned observations mapping FIPS (`geoId/{fips}`), year, StatVar (`Count_MortalityEvent_<Cause>`), and death count.
* `output/underlyingcauseofdeath_county.tmcf`: Template MCF mapping CSV columns to Data Commons Knowledge Graph entities.

---

### Operational Notes & Downloader Architecture

* **Static Historical Copy (`1999–2017`)**: Because historical `1999–2017` data is frozen, `download.py` copies `UnderlyingCauseofDeath_County_1999_2017.csv` directly from `gs://unresolved_mcf/cdc/UnderlyingCause/county_mortality_underlyingCause/input_files` into `input_files/` in seconds, avoiding ~4.5 hours of live historical queries on recurring runs.
* **Rate-Limit Handling (HTTP 429)**: CDC WONDER enforces a 30-minute IP block when query thresholds are exceeded. The downloader detects HTTP 429 responses, pauses in complete silence for 31 minutes (`1,860s`), and automatically refreshes the session before resuming. Do not terminate the process during this cooldown.
* **Large State Partitioning**: High-population states (e.g. California `06`, Florida `12`, New York `36`, Texas `48`) exceed CDC WONDER's 75,000-row query cap when queried across all years at once. The downloader automatically queries these states in 2-year chunks (or 1-year chunks for Texas) to prevent HTTP 400 ("Too Much Data") and HTTP 504 timeouts.
* **Stale Partition Cleanup**: When a state is re-downloaded, the downloader purges existing chunk and combined files for that state before writing new data, preventing duplicate observations when `stat_var_processor.py` processes `input_files/*.csv`.
* **Failure Isolation**: If an individual state query encounters network or server errors, the downloader logs the failure, continues with the remaining states, and raises a summary exception at the end of the batch run to ensure non-zero exit code while preserving downloaded progress.
* **Lazy Session Initialization**: The session agreement with CDC WONDER is only initialized when at least one state actually requires downloading, avoiding unnecessary network calls during dry runs or when data is already cached.

---

### Validation

Validation is configured in `validation_config.json` (in addition to the default checks in `tools/import_validation/validation_config.json`):
* `check_max_date_freshness`: Enforces rolling date freshness (`CAST(MaxDate AS INTEGER) >= (EXTRACT(YEAR FROM CURRENT_DATE) - 3) AND total_svs >= 107`) across the 107 common cause-of-death StatVars (excluding the 16 rare causes) to ensure the latest published data is ingested relative to the annual publication lag.
* `check_max_date_rare_causes`: Enforces a baseline floor check (`>= 2000`, `>= 2001`, `>= 2004`, `>= 2023`, or `>= 2024` depending on the historical last-observed year, with `total_rare_svs >= 16`) for the 16 rare causes of death that do not appear in every year due to CDC `<10` county death suppression.

---

### Important Files

| File | Description |
|---|---|
| `download.py` | Copies `1999–2017` historical CSV from GCS and downloads `2018–present` live from CDC WONDER (`D158`). |
| `download_test.py` | Comprehensive unit test suite for GCS copy, download session management, and error handling. |
| `county_mortality_metadata.csv` | Metadata specifying header row offsets, frequency, and output columns. |
| `county_mortality_pvmap.csv` | Property-Value mapping resolving county FIPS and ICD-10 113 causes of death. |
| `manifest.json` | Automation manifest declaring scripts, inputs/outputs, cron schedule, and validation config. |
| `validation_config.json` | Configuration defining import validation rules (historical deletion and date freshness). |
| `test_data/` | Trimmed sample Delaware dataset and expected outputs for offline verification. |

---

### Testing

Run the unit test suite from this directory:
```bash
python3 -m unittest discover -v -s . -p "*_test.py"
```
