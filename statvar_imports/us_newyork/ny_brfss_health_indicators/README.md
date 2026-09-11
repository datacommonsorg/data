# New York BRFSS Health Indicators Data

## 1. Import Overview

This project processes and imports health indicator prevalence rates across all 62 counties in New York State and New York City, provided by the New York State Department of Health. The dataset provides annual county-level estimates across 5 survey releases (2014, 2016, 2018, 2021, and 2024).

*   **Source URL**: [https://health.data.ny.gov/Health/Behavioral-Risk-Factor-Surveillance-System-BRFSS-H/jsy7-eb4n/about_data](https://health.data.ny.gov/Health/Behavioral-Risk-Factor-Surveillance-System-BRFSS-H/jsy7-eb4n/about_data)
*   **Import Type**: Automated
*   **Source Data Availability**: Data is available for 2014, 2016, 2018, 2021, and 2024.
*   **Release Frequency**: Periodic survey releases (biennial / triennial survey waves).
*   **Notes**: This dataset provides county-level estimates across 75 health indicators spanning chronic disease, mental health, substance use, disability, immunizations, and social determinants of health. The data originates from the Behavioral Risk Factor Surveillance System (BRFSS).

---

## 2. Preprocessing Steps

The import process involves querying the NYSDOH Socrata API and running a processing script on downloaded source data to generate the final artifacts for ingestion.

*   **Input files**:
    *   `input_files/`: This directory contains the raw unpivoted data file (`ny_brfss_health_indicators_raw.csv`) containing all 17,700 records across all survey years (2014, 2016, 2018, 2021, 2024).
    *   `ny_brfss_health_indicators_metadata.csv`: Configuration file for the data processing script specifying column mappings, header row offset, and provenance URL.
    *   `ny_brfss_health_indicators_pv_map.csv`: Property-value mapping file used by the processor to map indicators and county locations to Data Commons entities.
    *   `validation_config.json`: Configuration defining historical deletion and date freshness validation rules.
    *   `test_data/`: Sample input data and expected output files for integration testing.

*   **Transformation pipeline**:
    1.  The raw data is queried from the NYSDOH Socrata API using deterministic pagination (`$order: ':id'`) via `download.py` and placed in the `input_files/` directory.
    2.  The `stat_var_processor.py` tool is run on the raw data against `ny_brfss_health_indicators_pv_map.csv` and `ny_brfss_health_indicators_metadata.csv`, referencing canonical schema `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.
    3.  The processor filters non-county regional rows, resolves county FIPS DCIDs, maps indicators to canonical or provisional StatVars, and generates the final `ny_brfss_health_indicators_output.csv`, `ny_brfss_health_indicators_output.tmcf`, and supporting StatVar and schema MCF files in the `output_files/` directory.
    4.  Processor statistics and metrics are recorded in `counters/ny_brfss_health_indicators_counters.csv`.

*   **Data Quality Checks**:
    *   The `dc_generated/` directory contains `report.json` and `summary_report.csv`, which provide validation and summary statistics for the generated data.
    *   Automated validation via `validator.py` evaluates the output against `validation_config.json` enforcing the historical deletion threshold (<= 0.1%) and date freshness (`CAST(MaxDate AS INTEGER) >= (EXTRACT(YEAR FROM CURRENT_DATE) - 3)`).

---

## 3. Automated Import

This import is designed to be fully automated and autorefreshed. Future survey releases are automatically queried, processed, and validated.

### Automated Steps
1. The automated job triggers annually based on cron schedule `0 0 1 8 *` configured in `manifest.json`.
2. `download.py` queries the NYSDOH Socrata API endpoint with deterministic pagination (`$order: ':id'`) and updates `input_files/ny_brfss_health_indicators_raw.csv`.
3. `stat_var_processor.py` executes to regenerate the output CSV, TMCF, and MCF artifacts.
4. `validator.py` enforces validation rules from `validation_config.json` before publication.

---

## 4. Script Execution Details

To run the import pipeline, execute the processing scripts as detailed below.

### Download the Data

This script downloads the multi-year health indicators dataset from the NYSDOH Socrata API into `input_files/`:

**Usage**:
```bash
python3 download.py
```

### Process the Data

This script processes the raw input file to generate the final `ny_brfss_health_indicators_output.csv` file, `ny_brfss_health_indicators_output.tmcf` template, and supporting MCF files.

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="input_files/ny_brfss_health_indicators_raw.csv" \
  --pv_map=ny_brfss_health_indicators_pv_map.csv \
  --config_file=ny_brfss_health_indicators_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/ny_brfss_health_indicators_output \
  --output_counters=counters/ny_brfss_health_indicators_counters.csv
```

### Run Sample Integration Test

This script verifies property-value mapping against the test data fixtures:

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="test_data/sample_input.csv" \
  --pv_map=ny_brfss_health_indicators_pv_map.csv \
  --config_file=ny_brfss_health_indicators_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=test_data/sample_expected_output
```
