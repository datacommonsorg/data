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

The download script (`download_poverty.py`) downloads the official `EDA_FY23_PPCs.xlsx` workbook directly from EDA (with automatic fallback to the Wayback Machine archive mirror if Cloudflare bot detection blocks automated requests, or from a local file via `--input_file`) into `input_files/EDA_FY23_PPCs.xlsx`. It extracts the `Underlying_Data` sheet (3,241 rows) into `input_files/Poverty.csv`, which is then processed directly by `stat_var_processor.py` using `poverty_pvmap.csv` and `poverty_metadata.csv`.

The dataset benchmarks poverty rates across statutory periods:
- **1990**: 1990 Decennial Census (`year=1990`)
- **2000**: 2000 Decennial Census (`year=2000`)
- **2020**: 2020 Island Areas Decennial Census (`year=2020` for 11 territory county equivalents across FIPS prefixes `60`, `66`, `69`, `78`)
- **2021**: 2021 Small Area Income and Poverty Estimates (`"SAIPE, 2021"`, `year=2021` for 3,143 counties across all 50 states and DC) and 2017–2021 ACS 5-Year Estimates (`"ACS 5-YEAR, 2017-2021"`, `year=2021` for all 78 Puerto Rico municipios; `3,143 + 78 = 3,221`)

It covers 3,232 U.S. counties, county equivalents, and island territories (`3,143` state/DC counties + `78` Puerto Rico municipios + `11` island territory county equivalents). Island territories in the EDA dataset use 5-digit county-equivalent FIPS codes (e.g., 60010 for Eastern District, AS; 66010 for Guam; 69085 for Northern Islands, MP; 78010 for St. Croix, VI).

> [!NOTE]
> Direct automated HTTP requests to `eda.gov` may encounter Cloudflare bot protection (HTTP 403 Forbidden). `download_poverty.py` automatically falls back to an archive mirror of the official FY23 workbook. For manual/semi-automated refresh when upstream releases a new workbook, operators can download via a browser and provide it locally via `--input_file`.
>
> **Legacy `Commerce_EDA` Migration Note:** This standalone `Commerce_EDA_Poverty` import (`dc/base/Commerce_EDA_Poverty`) splits the Persistent Poverty Counties table out of the legacy combined `Commerce_EDA` import (`statvar_imports/commerce_eda`, alongside `Commerce_EDA_USAspending`). In accordance with Data Commons migration practice, the legacy `Commerce_EDA` import is retained temporarily until all split imports are merged and verified in production, and will be retired in an immediate follow-up cleanup PR/CL tracked under `b/548896854`.

### Direct PV Mapping Design (`poverty_pvmap.csv` & `poverty_metadata.csv`)

`stat_var_processor.py` processes the raw extracted `input_files/Poverty.csv` directly without a separate Python preprocessing script:
1. **Multi-Column (Wide-to-Long) Observation Emission**: Each numeric benchmark column (`1990 Decennial Census, % in Poverty`, `2000 Decennial Census, % in Poverty`, and `Most Recent Estimate, % in Poverty*`) maps `value: {Number}` and `variableMeasured: dcs:Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person`, emitting up to three `StatVarObservation` records per county row while inheriting row-level `observationAbout` from `GEOID`.
2. **Dynamic Observation Date & Measurement Method Resolution**: The `Data Source―Most Recent Estimate` column uses `#Regex` (`(?P<RecentSource>.*)[, -]+(?P<RecentYear>[0-9]{4}) *$`) and `#Eval` to dynamically resolve `{RecentYear}` and `{RecentMethod}` per row:
   - `"SAIPE, 2021"` (50 states and DC, 3,143 counties) $\rightarrow$ `observationDate: 2021`, `measurementMethod: dcs:EDA_Estimate`
   - `"ACS 5-YEAR, 2017-2021"` (Puerto Rico, 78 municipios) $\rightarrow$ `observationDate: 2021`, `measurementMethod: dcs:EDA_Estimate`
   - `"Decennial Census, 2020"` (Island territories, 11 county equivalents) $\rightarrow$ `observationDate: 2020`, `measurementMethod: dcs:USDecennialCensus`
3. **Header Handling, GEOID Zero-Padding & Filtering**:
   - `poverty_metadata.csv` sets `header_rows,3` so the 2-row title banner is treated as preamble and Row 3 is used as the column header; trailing free-text source/footnote rows contain no numeric cells in mapped observation columns and are automatically ignored.
   - `GEOID` uses `#Eval` (`observationAbout = 'geoId/' + str(int(Number)).zfill(5)`) to zero-pad 4-digit FIPS codes and `#Filter` (`not observationAbout.endswith('000')`) to exclude state-level summary rollups, while `filter_data_min_value,0` and `filter_data_max_value,100` enforce valid percentage bounds $[0.0, 100.0]$.

---

## Statistical Variable

```mcf
Node: dcid:Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person
typeOf: dcid:StatisticalVariable
name: "Population: Below Poverty Level in The Past 12 Months (Per Capita)"
populationType: dcid:Person
measuredProperty: dcid:count
statType: dcid:measuredValue
measurementDenominator: dcs:Count_Person
povertyStatus: dcid:BelowPovertyLevelInThePast12Months
```

---

## Working Directory Context

Commands in this workflow depend on the working directory:
- **Module directory (`statvar_imports/commerce_eda_poverty/`)**: Execute download and pipeline scripts (`download_poverty.py`, `stat_var_processor.py`).
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
Run from `statvar_imports/commerce_eda_poverty/`. Downloads the official `EDA_FY23_PPCs.xlsx` workbook directly from EDA (or archive mirror / local input file) and extracts the `Underlying_Data` sheet to `input_files/Poverty.csv`:
```bash
cd statvar_imports/commerce_eda_poverty
python3 download_poverty.py
```

To ingest a local copy directly without downloading:
```bash
python3 download_poverty.py --input_file=input_files/EDA_FY23_PPCs.xlsx
```

### 2. Generate Data Commons Observations (`stat_var_processor.py`)
Run from `statvar_imports/commerce_eda_poverty/`. Matches the scripts configured in `manifest.json`:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/Poverty.csv \
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
