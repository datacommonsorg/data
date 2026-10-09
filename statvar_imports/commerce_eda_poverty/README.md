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
| Place ID resolution | `country/USA` FIPS (5-digit county and county-equivalent FIPS codes, `geoId/XXXXX`) |
| Date range covered | 1990, 2000, 2020, 2021 (1990 Decennial Census, 2000 Decennial Census, 2020 Island Area Decennial Census, 2017–2021 ACS 5-Year) |
| Statistical Variables | `Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person` |
| Unit / Scaling | `Percent` / `100` |
| Refresh Cycle | Annual automated check (`30 05 1 1 *`) aligned with EDA/Census releases |

---

## Overview

This automated dataset import fetches and processes historical and recent county-level poverty percentage rates published by the U.S. Economic Development Administration (EDA) (`https://www.eda.gov/performance/resources/persistent-poverty-counties`) for Persistent Poverty Counties (PPCs) and all benchmarked U.S. counties.

The download script (`download_poverty.py`) downloads the official `EDA_FY23_PPCs.xlsx` workbook directly from EDA (with automatic fallback to the Wayback Machine archive mirror if Cloudflare bot detection blocks automated requests, or from a local file via `--input_file`) into `input_files/EDA_FY23_PPCs.xlsx`. It extracts the `Underlying_Data` sheet (3,241 county rows) into `input_files/Poverty.csv` and `output/Poverty_original.csv`.

The preprocessing script (`process_poverty.py`) reads the downloaded source file locally, cleans and standardizes 5-digit FIPS codes and poverty percentages into normalized `(GEOID, year, poverty_rate)` records in `output/Poverty_cleaned.csv`, and feeds the cleaned data into `stat_var_processor.py`. Neither script relies on Google Cloud Storage (GCS) staging.

The dataset benchmarks poverty rates across statutory periods:
- **1990**: 1990 Decennial Census (`year=1990`)
- **2000**: 2000 Decennial Census (`year=2000`)
- **2020**: 2020 Island Areas Decennial Census (`year=2020` for territory county equivalents `60`, `66`, `69`, `78`)
- **2021**: 2021 SAIPE / 2017–2021 ACS 5-Year Estimates (`year=2021` for all 50 states, DC, and Puerto Rico)

It covers 3,232 U.S. counties, county equivalents, and island territories. Island territories in the EDA dataset use 5-digit county-equivalent FIPS codes (e.g., 60010 for Eastern District, AS; 66010 for Guam; 69085 for Northern Islands, MP; 78010 for St. Croix, VI).

> [!NOTE]
> Direct automated HTTP requests to `eda.gov` may encounter Cloudflare bot protection (HTTP 403 Forbidden). `download_poverty.py` automatically falls back to an archive mirror of the official FY23 workbook. For manual/semi-automated refresh when upstream releases a new workbook, operators can download via a browser and provide it locally via `--input_file`.

### Why Preprocessing is Required (Why PV Map Alone is Insufficient)

The raw EDA dataset cannot be mapped directly into Data Commons observations using `stat_var_processor.py` / `poverty_pvmap.csv` alone because:
1. **Format Reshaping (Wide to Long)**: The raw sheet contains one row per county with multiple poverty percentage columns corresponding to different time periods (`1990 Decennial Census, % in Poverty`, `2000 Decennial Census, % in Poverty`, and `Most Recent Estimate, % in Poverty*`). PV mapping requires normalized long-format records with explicit observation dates.
2. **Dynamic & Heterogeneous Observation Dates**: The "Most Recent Estimate" is not uniform across places:
   - For all 50 U.S. states, DC, and Puerto Rico, the benchmark is SAIPE 2021 (`year=2021`).
   - For Island Territories (American Samoa, Guam, Northern Mariana Islands, U.S. Virgin Islands: FIPS prefixes `60`, `66`, `69`, `78`), SAIPE does not produce estimates; the benchmark is the 2020 Island Areas Decennial Census (`year=2020`).
   - The survey year is either conditionally determined by territory FIPS or parsed dynamically from the `Data Source―Most Recent Estimate` column (`"SAIPE, 2021"` vs `"Decennial Census, 2020"`). PV map CSV configurations cannot conditionally branch date assignment based on state FIPS code or evaluate regex over free-text notes.
3. **Data Cleaning & Filtering**:
   - Upstream Excel/CSV files contain non-tabular preamble headers, subtitles, and footnote rows that must be stripped.
   - Raw county FIPS codes in Excel often drop leading zeros (e.g. `1001` instead of `01001`) and include state-level summary rollups (e.g. `01000` for Alabama statewide) that must be filtered out so they are not ingested as county entities.

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

To ingest a local copy directly without downloading:
```bash
python3 download_poverty.py --input_file=input_files/EDA_FY23_PPCs.xlsx
```

### 2. Preprocess Dataset (`process_poverty.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Ingests the downloaded source file locally, standardizes 5-digit county and county-equivalent island territory FIPS codes, partitions the recent rates into 2020 (island territories) and 2021 (states, DC, PR), validates survey year bounds [2020..current year], enforces percentage value bounds $[0.0, 100.0]$, and atomically outputs `output/Poverty_cleaned.csv`:
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

After running the Data Commons `import_tool` (`genmcf` and differ steps, which produce `summary_report.csv`, `report.json`, and `differ_summary.json`), validate the generated outputs using the Import Validation Framework and `validation_config.json`. Run from the repository root `data/`:
```bash
python3 -m tools.import_validation.runner \
  --validation_config=statvar_imports/commerce_eda_poverty/validation_config.json \
  --stats_summary=statvar_imports/commerce_eda_poverty/output/summary_report.csv \
  --differ_output=statvar_imports/commerce_eda_poverty/output \
  --lint_report=statvar_imports/commerce_eda_poverty/output/report.json \
  --validation_output=statvar_imports/commerce_eda_poverty/output/validation_report.json
```

## Testing

Run unit tests verifying workbook download and mirror failover, local file ingestion, GEOID standardization, and value sanitation from the repository root `data/`:
```bash
python3 -m unittest discover -s statvar_imports/commerce_eda_poverty -p "*test*.py"
```
Or via the test runner script:
```bash
./run_tests.sh -p statvar_imports/commerce_eda_poverty
```
