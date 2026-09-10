# Commerce EDA Poverty: Persistent Poverty County Status and Rates

Author: Shivangi Singh  
Date: *September 2026*

| Parameter | Details |
| :--- | :--- |
| Link to dataset preview or raw data | [Treasury CDFI Geographic Reports](https://www.cdfifund.gov/documents/geographic-reports) / [EDA PPCs](https://www.eda.gov/performance/disclaimers) |
| Place types covered | U.S. Counties and County Equivalents (`County`) |
| Place ID resolution | `country/USA` county FIPS (`geoId/XXXXX`) |
| Date range covered | 1990, 2000, 2021 (1990 Decennial Census, 2000 Decennial Census, 2021 Census SAIPE / ACS) |
| Statistical Variables | `Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person` |
| Unit / Scaling | `Percent` / `100` |
| Refresh Cycle | Periodic / Decadal (aligned with EDA/Census benchmark releases) |
| GCS Source Path | `gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv` |

---

## Overview

This dataset import contains historical and recent county-level poverty percentage rates compiled by the U.S. Economic Development Administration (EDA) and Treasury CDFI Fund for evaluating Persistent Poverty County (PPC) status. The dataset benchmarks county poverty rates across three official periods:
- **1990**: 1990 Decennial Census
- **2000**: 2000 Decennial Census
- **2021**: 2021 Small Area Income and Poverty Estimates (SAIPE) / American Community Survey (ACS 5-Year)

The dataset covers all ~3,143 U.S. counties and island territories with valid 5-digit FIPS codes (`01` through `56`, `60`, `66`, `69`, `72`, `78`).

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

## Pipeline Execution

### Prerequisites
Ensure python dependencies and google cloud storage utilities are available:
```bash
pip install pandas absl-py duckdb
```

### 1. Preprocess Raw Dataset (`process_poverty.py`)
Downloads `Poverty.csv` from GCS (`gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`), cleans and normalizes headers, standardizes FIPS codes with state prefix validation, enforces value bounds $[0.0, 100.0]$, and atomically outputs `output/Poverty_cleaned.csv`:
```bash
python3 process_poverty.py
```

### 2. Generate Data Commons Observations (`stat_var_processor.py`)
Runs the Data Commons StatVar processor to generate cleaned observations and template MCF:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=output/Poverty_cleaned.csv \
  --pv_map=Povertypvmap.csv \
  --config_file=Povertymetadata.csv \
  --output_path=output/Poverty_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_counters=counters/Poverty_counters.csv
```

## Future Updates
- The preprocessing script (`process_poverty.py`) copies the source file from GCS. In future release cycles, if the source file in `gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv` is updated, running the script will automatically process the updated data. If the source portal structure or URL changes, the script may need to be updated to fetch directly from the website.
