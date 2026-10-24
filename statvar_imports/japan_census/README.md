# Japan Census and Demographic Statistics Data

## 1. Import Overview

This project downloads, processes, and imports demographic, employment, education, health, and mortality statistics for Japan across National (`country/JPN`), Prefecture (`AdministrativeArea1`), and Municipality (`AdministrativeArea2`) geographic levels, provided by the Official Statistics of Japan (e-Stat Statistical Dashboard).

*   **Source URL**: [https://dashboard.e-stat.go.jp/en/](https://dashboard.e-stat.go.jp/en/)
*   **API Endpoint**: `https://dashboard.e-stat.go.jp/api/1.0/Json/getData`
*   **Import Type**: Automated
*   **Source Data Availability**:
    *   **Population Census (National & Prefecture)**: 5-year census waves (`1920`–`2025`).
    *   **Population Census (Municipality)**: 5-year census waves (`1980`–`2025`).
    *   **Employment & Unemployment Rate (National)**: Annual (`1953`–`2025`).
    *   **Student Enrollment (National)**: Annual (`1948`–`2026`).
    *   **Teachers (National & Prefecture)**: Annual (`1975`–`2024`).
    *   **Deaths (National & Prefecture)**: Annual (`1975`–`2025`).
    *   **Causes of Death (National & Prefecture)**: Annual (`1975`–`2023`).
*   **Release Frequency**: Annual (vital, labor, and education statistics) and quinquennial (5-year Population Census).
*   **Notes**: This dataset covers 101 StatisticalVariables across 1,965 places (`country/JPN`, 47 Prefectures, and 1,917 Municipalities).

---

## 2. Preprocessing Steps

The import pipeline queries the e-Stat Statistical Dashboard JSON API in parallel to download raw datasets as-is, and then `process.py` preprocesses Census broad age sums, merges historical archival records from `gs://unresolved_mcf/country/japan/deleted_historical_data.csv`, and runs `stat_var_processor.py` across shards in parallel.

*   **Files**:
    *   `download_script.py`: Queries the e-Stat Statistical Dashboard API (`https://dashboard.e-stat.go.jp/api/1.0/Json/getData`) and writes the 9 raw CSV dataset files as-is into `input_files/` without preprocessing.
    *   `process.py`: Preprocesses raw input files (computes exact broad age-group sums for Census datasets, merges historical records from `gs://unresolved_mcf/country/japan/deleted_historical_data.csv`, and stages municipality census files by year), runs `stat_var_processor.py` across shards in parallel (`--parallelism=2`), and deterministically merges the resulting `.csv`, `.tmcf`, `.mcf`, and `counters.csv` outputs into `output_files/`.
    *   `japan_census_metadata.csv`: Configuration file for `stat_var_processor.py` specifying output columns, header rows, mapped columns, and provenance URL.
    *   `japan_census_pv_map.csv`: Property-value mapping file mapping e-Stat indicator codes (`indicatorCd`) and 5-digit region codes (`regionCd`) to Data Commons StatisticalVariables and place DCIDs (`country/JPN` and `wikidataId/Q...`).
    *   `validation_config.json`: Configuration defining historical deletion (`<= 0.1%`), value bounds, and date freshness validation rules across all 101 StatisticalVariables.
    *   `test_data/`: Sample input data (`sample_input.csv`) and expected output (`sample_expected_output.csv`) for testing.

*   **Transformation pipeline**:
    1.  `download_script.py` fetches all 9 raw datasets from the e-Stat JSON API as-is using concurrent workers and atomic file writes into `input_files/`.
    2.  `process.py` preprocesses the raw input CSVs in a temporary staging directory (deriving broad age sums for Census datasets, applying historical data supplements, and splitting municipality census data by year) and invokes `stat_var_processor.py` in parallel across the staged input CSVs against `japan_census_pv_map.csv` and `japan_census_metadata.csv`, referencing canonical schema `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.
    3.  The processor filters non-target regional aggregate rows via `#IgnoreRow`, resolves place DCIDs, and produces `output_files/japan_census_output.csv` and `output_files/japan_census_output.tmcf`. To preserve 1:1 historical series continuity (`0` deleted / `0` modified records) with the legacy `Japan_Census` import:
        *   Labor force counts (`0301010000010010010`, `0301010000020010010`, `0301010000030010010`, reported by e-Stat in units of `10,000 persons`) apply `#Multiply,10` to match the historical scaling (in thousands).
        *   Indicator `1201040500000010000` (`Number of upper secondary school teachers (full-time)`) maps to `dcid:Count_Teacher_UniversityAndCollegeTeacher` to match the legacy StatVar assignment across `1975`–`2021`.
    4.  Aggregated processor counters are written to `counters/japan_census_counters.csv`.

*   **Data Quality Checks**:
    *   Automated validation via `tools/import_validation/runner.py` evaluates the output against `validation_config.json`, enforcing:
        *   `check_deleted_records_percent`: Historical deletion threshold `<= 0.1%` (`0` deleted records).
        *   `check_max_date_freshness`: Verifies `MaxDate`, `NumPlaces >= 1`, `MinValue >= 0`, and rate bounds (`MaxValue <= 100` for `UnemploymentRate_Person`) across all 92 active recurring indicators.
        *   `check_max_date_historical_indicators`: Verifies `MaxDate >= 2020` and `MinValue >= 0` across the 9 discontinued centenarian sub-brackets (`100–104`, `105–109`, `110+`).
        *   `check_max_date_consistent_*`: Scoped `MAX_DATE_CONSISTENT` rules verifying uniform `MaxDate` within each co-released survey group (Population Census, Labor Force & Deaths, Teachers, Students, Causes of Death, and Historical Centenarians).

---

## 3. Automated Import

This import is configured for automated monthly execution in `manifest.json`.

### Automated Steps
1. The automated job triggers on cron schedule `0 5 1 * *` configured in `manifest.json`.
2. `download_script.py` queries the e-Stat Dashboard API and populates `input_files/*.csv`.
3. `process.py` runs `stat_var_processor.py` with `--parallelism=2` to generate `output_files/japan_census_output.csv` and `output_files/japan_census_output.tmcf`.
4. Validation rules in `validation_config.json` are evaluated before publication.

---

## 4. Script Execution Details

To run the import pipeline locally from `statvar_imports/japan_census/`:

### Download the Data

```bash
python3 download_script.py
```

### Process the Data

```bash
python3 process.py \
  --input_data=input_files/*.csv \
  --pv_map=japan_census_pv_map.csv \
  --config_file=japan_census_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/japan_census_output \
  --output_counters=counters/japan_census_counters.csv \
  --parallelism=2
```

### Run Sample Integration Test

```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/sample_input.csv \
  --pv_map=japan_census_pv_map.csv \
  --config_file=japan_census_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=test_data/sample_expected_output
```

### Run Unit Tests

```bash
python3 -m unittest discover -s . -p "*_test.py" -v
```
