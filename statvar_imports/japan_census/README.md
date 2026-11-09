# Japan Census and Demographic Statistics Data

## 1. Import Overview

This project downloads, processes, and imports demographic, employment, education, health, and mortality statistics for Japan across National (`country/JPN`), Prefecture (`AdministrativeArea1`), and Municipality (`AdministrativeArea2`) geographic levels, provided by the Portal Site of Official Statistics of Japan (e-Stat).

*   **Source URL**: [https://www.e-stat.go.jp/](https://www.e-stat.go.jp/)
*   **Endpoints**:
    *   `https://www.e-stat.go.jp/dbview?sid=...` (e-Stat Database View raw CSV download)
    *   `https://dashboard.e-stat.go.jp/download/dataSearch` (e-Stat Statistics Dashboard raw CSV Batch Download)
*   **Import Type**: Automated
*   **Source Data Availability**:
    *   **Population Census (National & Prefecture)**: 5-year census waves (`1920`–`2020`, `sid=0003410380` and `sid=0003410381`).
    *   **Population Census (Municipality)**: 5-year census waves (`1980`–`2020`, `sid=0003412413`..`0003412420` and `sid=0003448299`).
    *   **Employment & Unemployment Rate (National)**: Annual (`1953`–`2025`, Dashboard `dataSearch`).
    *   **Student Enrollment (National)**: Annual (`1948`–`2026`, Dashboard `dataSearch`).
    *   **Teachers (National & Prefecture)**: Annual (`1975`–`2024`, `sid=0000010105`).
    *   **Deaths (National & Prefecture)**: Annual (`1975`–`2023`, `sid=0000010101`).
    *   **Causes of Death (National & Prefecture)**: Annual (`1975`–`2023`, `sid=0000010109`).
*   **Release Frequency**: Annual (vital, labor, and education statistics) and quinquennial (5-year Population Census).
*   **Notes**: This dataset covers 83 StatisticalVariables across 1,965 places (`country/JPN`, 47 Prefectures, and 1,917 Municipalities).

---

## 2. Preprocessing Steps

The import pipeline downloads all 17 raw CSV tables directly from e-Stat (`https://www.e-stat.go.jp/dbview?sid=...` and `https://dashboard.e-stat.go.jp/download/dataSearch`) into `input_files/` and processes them directly with `tools/statvar_importer/stat_var_processor.py` without custom preprocessing scripts.

*   **Files**:
    *   `download_script.py`: Downloads all 17 raw CSV tables directly from e-Stat `dbview` and Dashboard `dataSearch` into `input_files/`.
    *   `japan_census_metadata.csv`: Configuration file for `stat_var_processor.py` specifying `output_columns`, `mapped_rows,12`, and `mapped_columns,5`.
    *   `japan_census_pv_map.csv`: Property-value mapping file mapping e-Stat Japanese age/gender/metric headers, time codes, and 5-digit region codes (`01000`–`47382`) to Data Commons StatisticalVariables and place DCIDs (`country/JPN` and `wikidataId/Q...`).
    *   `validation_config.json`: Configuration defining value bounds and date freshness validation rules.
    *   `test_data/`: Sample input data (`sample_input.csv`) and expected outputs (`sample_expected_output.csv`, `sample_expected_output.tmcf`) for testing.

*   **Transformation pipeline**:
    1.  `download_script.py` fetches all 17 raw CSV files into `input_files/`.
    2.  `tools/statvar_importer/stat_var_processor.py` processes `input_files/*.csv` directly using `japan_census_pv_map.csv` and `japan_census_metadata.csv`, referencing canonical schema `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.
    3.  The processor produces `output_files/japan_census_output.csv`, `output_files/japan_census_output.tmcf`, and `counters/japan_census_counters.csv`.

*   **Data Quality Checks**:
    *   Automated validation via `tools/import_validation/runner.py` evaluates the output against `validation_config.json` (alongside the default `<= 0.1%` historical deletion threshold), enforcing:
        *   `check_max_date_freshness`: Verifies `MaxDate`, `NumPlaces >= 1`, `MinValue >= 0`, and rate bounds (`MaxValue <= 100` for `UnemploymentRate_Person`) across all 83 indicators.
        *   `check_max_date_consistent_*`: Scoped `MAX_DATE_CONSISTENT` rules verifying uniform `MaxDate` within each co-released survey group (Population Census, Labor Force Survey, Teachers, Students, and Vital Statistics).

---

## 3. Automated Import

This import is configured for automated weekly execution in `manifest.json`.

### Automated Steps
1. The automated job triggers on cron schedule `0 5 * * 1` configured in `manifest.json`.
2. `download_script.py` downloads the raw CSV tables into `input_files/*.csv`.
3. `stat_var_processor.py` processes `input_files/*.csv` to generate `output_files/japan_census_output.csv` and `output_files/japan_census_output.tmcf`.
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
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/*.csv \
  --pv_map=japan_census_pv_map.csv \
  --config_file=japan_census_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/japan_census_output \
  --output_counters=counters/japan_census_counters.csv
```

### Run Sample Integration Test (Offline)

```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/sample_input.csv \
  --pv_map=japan_census_pv_map.csv \
  --config_file=japan_census_metadata.csv \
  --existing_statvar_mcf=/dev/null \
  --output_path=test_data/sample_expected_output
```

### Run Unit Tests

```bash
python3 -m unittest discover -s . -p "*_test.py" -v
```
