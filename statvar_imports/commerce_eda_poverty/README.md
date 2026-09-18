# Commerce EDA Poverty: Persistent Poverty County Status and Rates

Author: Shivangi Singh  
Date: *September 2026*

| Parameter | Details |
| :--- | :--- |
| Import Type | **Semi-Automated Import** (raw workbook manually downloaded from source and staged to GCS) |
| Link to dataset preview or raw data | [Treasury CDFI Geographic Reports](https://www.cdfifund.gov/documents/geographic-reports) / [EDA PPCs](https://www.eda.gov/performance/disclaimers) |
| Place types covered | U.S. Counties and County Equivalents (`County`) |
| Place ID resolution | `country/USA` county FIPS (`geoId/XXXXX`) |
| Date range covered | 1990, 2000, 2020, 2021 (1990 Decennial Census SF3, 2000 Decennial Census SF3, 2020 Decennial Census for Island Areas, 2021 SAIPE / ACS) |
| Statistical Variables | `Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person` |
| Unit / Scaling | `Percent` / `100` |
| Refresh Cycle | Periodic / Decadal (aligned with EDA/Census benchmark releases) |
| GCS Source Path | `gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv` |

---

## Overview

This dataset import (**semi-automated import**) contains historical and recent county-level poverty percentage rates compiled by the U.S. Economic Development Administration (EDA) and Treasury CDFI Fund for evaluating Persistent Poverty County (PPC) status. Because the upstream source publishes an Excel workbook on a periodic/decadal release schedule without a direct programmatic API, the raw county sheet is downloaded from the official source and staged to Google Cloud Storage (`gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`), from which the automated processing pipeline (`process_poverty.py` and `stat_var_processor.py`) ingests and validates the data.

The dataset benchmarks county poverty rates across official periods:
- **1990**: 1990 Decennial Census SF3
- **2000**: 2000 Decennial Census SF3
- **2020**: 2020 Decennial Census for Island Areas (American Samoa, Guam, Northern Mariana Islands, US Virgin Islands)
- **2021**: 2021 SAIPE (50 US States + DC) / 2017–2021 ACS 5-Year (Puerto Rico)

The dataset covers all ~3,232 U.S. counties and island territories with valid 5-digit FIPS codes (`01` through `56`, `60`, `66`, `69`, `72`, `78`).

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
- **Module directory (`statvar_imports/commerce_eda_poverty/`)**: Execute preprocessing and pipeline scripts (`process_poverty.py`, `stat_var_processor.py`).
- **Repository root (`data/`)**: Execute validation runner, test scripts (`./run_tests.sh`), and unittest module invocations.

---

## Pipeline Execution (Semi-Automated Import Setup)

### Prerequisites
Ensure python dependencies and Google Cloud SDK are available:
```bash
pip install pandas absl-py duckdb
```

### 0. Source Data Download & GCS Staging Setup (Semi-Automated Step)
Because the upstream dataset is hosted as a static workbook on the U.S. Department of the Treasury CDFI Fund portal, perform the following setup steps whenever a new Persistent Poverty Counties (PPC) release is published:
1. **Download Official Workbook**: Visit the [Treasury CDFI Fund Geographic Reports page](https://www.cdfifund.gov/documents/geographic-reports) and download the **Persistent Poverty Counties** Excel file (e.g., `PPC-by-2020-Census-Tracts.xlsx` / *Persistent Poverty Counties* workbook).
2. **Export County Tab as CSV**: Open the county-level worksheet (`Poverty` / County tab containing columns `Name`, `GEOID`, `1990 Decennial Census, % in Poverty`, `2000 Decennial Census, % in Poverty`, `Most Recent Estimate, % in Poverty*`, and `Data Source―Most Recent Estimate`, preserving the 2 leading title rows) and export/save it as UTF-8 CSV named `Poverty.csv`.
3. **Upload to GCS Staging Bucket**: Copy `Poverty.csv` to the GCS input path configured in `process_poverty.py`:
   ```bash
   gcloud storage cp Poverty.csv gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv
   ```

### 1. Preprocess Raw Dataset (`process_poverty.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Downloads `Poverty.csv` from GCS (`gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`), cleans and normalizes headers, standardizes FIPS codes with state prefix validation, verifies survey years, enforces value bounds $[0.0, 100.0]$, and atomically outputs `output/Poverty_cleaned.csv`:
```bash
cd statvar_imports/commerce_eda_poverty
python3 process_poverty.py
```

### 2. Generate Data Commons Observations (`stat_var_processor.py`)
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

## Testing

Run unit tests verifying GEOID standardization, out-of-bounds sanitation, and pipeline processing (including exact comparison of `test_data/Poverty_input.csv` against `test_data/Poverty_expected_output.csv`) from the repository root `data/`:
```bash
python3 -m unittest statvar_imports.commerce_eda_poverty.process_poverty_test
```
Or via the test runner script:
```bash
./run_tests.sh -p statvar_imports/commerce_eda_poverty
```

---

## Maintenance & Upstream Refresh Workflow

This is a **semi-automated import**. When a new PPC benchmark or update is released by EDA or Treasury CDFI:
1. **Download & stage source file to GCS**: Download the updated workbook from [Treasury CDFI Geographic Reports](https://www.cdfifund.gov/documents/geographic-reports), export the County tab as `Poverty.csv`, and upload it to `gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`.
2. **Preprocess data**: In `statvar_imports/commerce_eda_poverty/`, run `python3 process_poverty.py` to verify schema, survey years, and row count sanity thresholds ($\ge 3,000$ counties).
3. **Generate observations**: Run `stat_var_processor.py` and verify zero errors in `counters/Poverty_counters.csv`.
4. **Validate & Test**: From the repository root `data/`, run the import validation runner and unit tests to ensure all thresholds and validation rules pass.
