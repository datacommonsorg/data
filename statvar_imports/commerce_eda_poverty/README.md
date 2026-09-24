# Commerce EDA Poverty: Persistent Poverty County Status and Rates

Author: Shivangi Singh  
Date: *September 2026*

| Parameter | Details |
| :--- | :--- |
| Import Type | **Automated Import** (raw dataset downloaded directly from source website or local input file, and processed locally) |
| Link to dataset preview or raw data | [EDA Persistent Poverty Counties](https://www.eda.gov/performance/resources/persistent-poverty-counties) |
| Direct Workbook URL | [`EDA_FY23_PPCs.xlsx`](https://www.eda.gov/sites/default/files/2023-03/EDA_FY23_PPCs.xlsx) |
| Archive Mirror URL | [`EDA_FY23_PPCs.xlsx` (Wayback Machine)](https://web.archive.org/web/20250308204521if_/https://www.eda.gov/sites/default/files/2023-03/EDA_FY23_PPCs.xlsx) |
| Place types covered | U.S. Counties, County Equivalents, and Island Territories (`County` / `AdministrativeArea1`) |
| Place ID resolution | `country/USA` FIPS (`geoId/XXXXX` for counties, `geoId/XX` for island territories) |
| Date range covered | 1990, 2000, 2020, 2021 (1990 Decennial Census, 2000 Decennial Census, 2020 Island Area Decennial Census, 2017–2021 ACS 5-Year) |
| Statistical Variables | `Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person` |
| Unit / Scaling | `Percent` / `100` |
| Refresh Cycle | Weekly automated check (`30 05 * * 1`) aligned with EDA/Census releases |

---

## Overview

This automated dataset import fetches and processes historical and recent county-level poverty percentage rates published by the U.S. Economic Development Administration (EDA) (`https://www.eda.gov/performance/resources/persistent-poverty-counties`) for Persistent Poverty Counties (PPCs) and all benchmarked U.S. counties.

The download script (`download_poverty.py` / `download.py`) downloads the official `EDA_FY23_PPCs.xlsx` workbook directly from EDA (with automatic fallback to the Wayback Machine archive mirror if Cloudflare bot detection blocks automated requests, or from a local file via `--input_file`) into `input_files/EDA_FY23_PPCs.xlsx`. It extracts the `Underlying_Data` sheet (3,241 county rows) into `input_files/Poverty.csv` and `output/Poverty_original.csv`.

The preprocessing script (`process_poverty.py`) reads the downloaded source file locally, cleans and standardizes FIPS codes and poverty percentages into `output/Poverty_cleaned.csv`, and feeds the cleaned data into `stat_var_processor.py`. Neither script relies on Google Cloud Storage (GCS) staging.

The dataset benchmarks poverty rates across statutory periods:
- **1990**: 1990 Decennial Census (`poverty_rate_1990`)
- **2000**: 2000 Decennial Census (`poverty_rate_2000`)
- **2020**: 2020 Island Areas Decennial Census (`poverty_rate_2020` for territories `60`, `66`, `69`, `78`)
- **2021**: 2017–2021 ACS 5-Year Estimates (`poverty_rate_2021` for all 50 states, DC, and Puerto Rico)

It covers 3,232 U.S. counties, county equivalents, and island territories.

---

## Statistical Variable

```mcf
Node: dcid:Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person
typeOf: dcid:StatisticalVariable
name: "Population: Below Poverty Level in The Past 12 Months (Per Capita)"
populationType: dcid:Person
measuredProperty: dcid:count
statType: dcid:measuredValue
measurementDenominator: dcid:Count_Person
povertyStatus: dcid:BelowPovertyLevelInThePast12Months
```

---

## Working Directory Context

Commands in this workflow depend on the working directory:
- **Module directory (`statvar_imports/commerce_eda_poverty/`)**: Execute download, preprocessing, and pipeline scripts (`download_poverty.py`, `process_poverty.py`, `stat_var_processor.py`).
- **Repository root (`data/`)**: Execute validation runner, test scripts (`./run_tests.sh`), and unittest module invocations.

---

## Pipeline Execution (Automated Import)

### Prerequisites
Ensure Python dependencies are available:
```bash
pip install pandas openpyxl requests absl-py duckdb
```

For running `stat_var_processor.py` locally, authenticate Google Cloud Application Default
Credentials to allow reading the central schema definitions from Google Cloud Storage:
```bash
gcloud auth application-default login
```
*(Required to read `--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`).*

### 1. Download Source Dataset (`download_poverty.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Downloads the official `EDA_FY23_PPCs.xlsx` workbook directly from EDA (or archive mirror / local input file) and extracts the `Underlying_Data` sheet to `input_files/Poverty.csv` (also staging `output/Poverty_original.csv`):
```bash
cd statvar_imports/commerce_eda_poverty
python3 download_poverty.py
```
*(An alias `python3 download.py` is also provided).*

To ingest a local copy directly without downloading:
```bash
python3 download_poverty.py --input_file=input_files/EDA_FY23_PPCs.xlsx
```

### 2. Preprocess Dataset (`process_poverty.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Ingests the downloaded source file locally, standardizes 5-digit county and 2-digit island territory FIPS codes, partitions the recent rates into 2020 (island territories) and 2021 (states, DC, PR), enforces percentage value bounds $[0.0, 100.0]$, and atomically outputs `output/Poverty_cleaned.csv`:
```bash
python3 process_poverty.py
```

### 3. Generate Data Commons Observations (`stat_var_processor.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Matches the scripts configured in `manifest.json`:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=output/Poverty_cleaned.csv \
  --pv_map=poverty_pvmap.csv \
  --config_file=poverty_metadata.csv \
  --output_path=output/Poverty_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_counters=counters/Poverty_counters.csv
```

---

## Validation

Validate generated outputs using the Import Validation Framework and `validation_config.json`. Run from the repository root `data/`:
```bash
python3 -m tools.import_validation.runner \
  --validation_config=statvar_imports/commerce_eda_poverty/validation_config.json \
  --stats_summary=statvar_imports/commerce_eda_poverty/dc_generated/summary_report.csv \
  --differ_output=statvar_imports/commerce_eda_poverty/dc_generated \
  --lint_report=statvar_imports/commerce_eda_poverty/dc_generated/report.json \
  --validation_output=statvar_imports/commerce_eda_poverty/dc_generated/validation_report.json
```

---

## Troubleshooting & Operational Runbook

### 1. Cloudflare Bot Detection / HTTP 403 Forbidden
- **Symptom:** `download_poverty.py` receives HTTP 403 when requesting EDA URLs.
- **Automatic Mitigation:** The script automatically catches non-200 responses and falls back to
  the Wayback Machine archive mirror (`EDA_PPC_MIRROR_URL`).
- **Manual Workaround:** Download the workbook manually via a browser from the official
  [EDA PPC page](https://www.eda.gov/performance/resources/persistent-poverty-counties) and
  pass it via `--input_file`:
  ```bash
  python3 download_poverty.py --input_file=input_files/EDA_FY23_PPCs.xlsx
  ```

### 2. Survey Year Mismatch / Upstream Schema Changes
- **Symptom:** `process_poverty.py` raises `ValueError: Unexpected survey year...`.
- **Cause:** EDA periodically releases updated PPC workbooks baselining newer Census/SAIPE
  estimates (e.g. transitioning from SAIPE 2021 to 2022 or 2023).
- **Remediation:**
  1. Inspect the new column headers and update the date mapping logic in `process_poverty.py`.
  2. Update `poverty_metadata.csv` and `poverty_pvmap.csv` if new column names are introduced.
  3. Update `validation_config.json` date span rules to accommodate the new maximum date.

### 3. County Count Threshold Failures
- **Symptom:** Validation fails on `NUM_PLACES_COUNT` outside `[3100, 3250]` or `process_poverty.py`
  raises `Cleaned county count below minimum threshold`.
- **Cause:** Upstream sheet layout changes (e.g., altered sheet name, modified header row
  offset, or unexpected GEOID formatting).
- **Remediation:** Check whether EDA modified the sheet structure or header rows. Re-run
  preprocessing and inspect `output/Poverty_cleaned.csv`.

---

## Testing

Run unit tests verifying website link discovery, workbook download and mirror failover, local file ingestion, GEOID standardization, and value sanitation from the repository root `data/`:
```bash
python3 -m unittest discover -s statvar_imports/commerce_eda_poverty -p "*test*.py"
```
Or via the test runner script:
```bash
./run_tests.sh -p statvar_imports/commerce_eda_poverty
```
