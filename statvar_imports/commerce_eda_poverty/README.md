# Commerce EDA Poverty: Persistent Poverty County Status and Rates

Author: Shivangi Singh  
Date: *September 2026*

| Parameter | Details |
| :--- | :--- |
| Import Type | **Automated Import** (raw dataset downloaded directly from source website and processed locally) |
| Link to dataset preview or raw data | [Treasury CDFI Geographic Reports](https://www.cdfifund.gov/documents/geographic-reports) |
| Direct Workbook URL | [`PPC_2020_ACS_May_10_2024.xlsx`](https://www.cdfifund.gov/system/files?file=2024-05/PPC_2020_ACS_May_10_2024.xlsx) |
| Place types covered | U.S. Counties, County Equivalents, and Island Territories (`County` / `AdministrativeArea1`) |
| Place ID resolution | `country/USA` FIPS (`geoId/XXXXX` for counties, `geoId/XX` for island territories) |
| Date range covered | 1990, 2000, 2020 (1990 Decennial Census, 2000 Decennial Census, 2016–2020 ACS 5-Year / Island Area Decennial Census) |
| Statistical Variables | `Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person` |
| Unit / Scaling | `Percent` / `100` |
| Refresh Cycle | Weekly automated check (`30 05 * * 1`) aligned with CDFI/Census releases |

---

## Overview

This automated dataset import fetches and processes historical and recent county-level poverty percentage rates published by the U.S. Department of the Treasury Community Development Financial Institutions (CDFI) Fund (`https://www.cdfifund.gov/documents/geographic-reports`) for Persistent Poverty Counties (PPCs).

The download script (`download_poverty.py` / `download.py`) dynamically discovers and downloads the latest Persistent Poverty Counties Excel workbook directly from the Treasury CDFI Fund website into `input_files/poverty_source.xlsx` (with an extracted raw CSV copy at `output/Poverty_original.csv`).

The preprocessing script (`process_poverty.py`) reads the downloaded source file locally, cleans and standardizes FIPS codes and poverty percentages into `output/Poverty_cleaned.csv`, and feeds the cleaned data into `stat_var_processor.py`. Neither script relies on Google Cloud Storage (GCS) staging.

The dataset benchmarks poverty rates across three statutory periods:
- **1990**: 1990 Decennial Census (`poverty_rate_1990`)
- **2000**: 2000 Decennial Census (`poverty_rate_2000`)
- **2020**: 2016–2020 ACS 5-Year / Island Areas Decennial Census (`poverty_rate_2020`)

It covers all 410 designated Persistent Poverty Counties and U.S. Island Territories (`407` 5-digit county/municipio FIPS codes across U.S. states and Puerto Rico, plus `3` 2-digit island territory FIPS codes: `60` American Samoa, `69` Northern Mariana Islands, and `78` U.S. Virgin Islands).

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

### 1. Download Source Dataset (`download_poverty.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Dynamically discovers and downloads the latest Persistent Poverty Counties `.xlsx` workbook from `https://www.cdfifund.gov/documents/geographic-reports` and saves it to `input_files/poverty_source.xlsx` (also exporting `output/Poverty_original.csv`):
```bash
cd statvar_imports/commerce_eda_poverty
python3 download_poverty.py
```
*(An alias `python3 download.py` is also provided).*

### 2. Preprocess Dataset (`process_poverty.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Ingests the downloaded source file locally, standardizes 5-digit county and 2-digit island territory FIPS codes, enforces percentage value bounds $[0.0, 100.0]$, and atomically outputs `output/Poverty_cleaned.csv`:
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

## Testing

Run unit tests verifying website link discovery, Excel workbook download, local file processing, GEOID standardization, and value sanitation from the repository root `data/`:
```bash
python3 -m unittest discover -s statvar_imports/commerce_eda_poverty -p "*test*.py"
```
Or via the test runner script:
```bash
./run_tests.sh -p statvar_imports/commerce_eda_poverty
```
