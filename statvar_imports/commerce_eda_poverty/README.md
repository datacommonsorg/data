# Commerce EDA Poverty: Persistent Poverty County Status and Rates

Author: Shivangi Singh  
Date: *September 2026*

| Parameter | Details |
| :--- | :--- |
| Import Type | **Semi-Automated** |
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

This dataset import contains historical and recent county-level poverty percentage rates compiled
by the U.S. Economic Development Administration (EDA) and Treasury CDFI Fund for evaluating
Persistent Poverty County (PPC) status. The dataset benchmarks county poverty rates across three
official periods:
- **1990**: 1990 Decennial Census
- **2000**: 2000 Decennial Census
- **2021**: 2021 Small Area Income and Poverty Estimates (SAIPE) / American Community Survey (ACS 5-Year)

The dataset covers all 3,232 U.S. counties and island territories with valid 5-digit FIPS codes
(`01` through `56`, `60`, `66`, `69`, `72`, `78`).

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

1. **Python Dependencies:**
   ```bash
   pip install pandas absl-py duckdb
   ```

2. **Google Cloud Authentication:**
   Access to `gs://unresolved_mcf/` requires application-default credentials:
   ```bash
   gcloud auth application-default login
   ```

### 1. Preprocess Raw Dataset (`process_poverty.py`)

Downloads `Poverty.csv` from GCS (`gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`) with
retry/backoff, dynamically parses the recent estimate year, standardizes FIPS codes with state
prefix validation, enforces value bounds $[0.0, 100.0]$, reshapes observations to long format
(`GEOID`, `observationDate`, `poverty_rate`), and atomically outputs `output/Poverty_cleaned.csv`:
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

### 3. Unit Tests

Run the hermetic test suite:
```bash
python3 -m unittest statvar_imports.commerce_eda_poverty.process_poverty_test
```

---

## Validation Configuration

Validation rules in `validation_config.json`:
- `check_percent_min_value`: Asserts poverty rate $\ge 0\%$.
- `check_percent_max_value`: Asserts poverty rate $\le 100\%$.
- `check_num_places_county_count`: Verifies county coverage (3,100 to 3,250 counties; 3,232 observed).
- `check_date_span_sql`: Asserts time series spans from 1990 through at least 2021.
- `check_missing_refs_count`: Ensures 0 unresolvable node/property references.
- `check_lint_error_count`: Ensures 0 syntax/lint errors in outputs.
- `check_deleted_records_percent`: Threshold set to `0.1` (0.1%), allowing for rare FIPS boundary
  re-organizations (such as Connecticut planning regions or Alaska census areas) while flagging
  unexpected historical data drops.

---

## Future Updates & Maintenance

1. When Treasury CDFI / EDA publishes an updated PPC dataset, download the latest Excel/CSV from
   [Treasury CDFI Geographic Reports](https://www.cdfifund.gov/documents/geographic-reports).
2. Upload the new source file to `gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`.
3. `process_poverty.py` dynamically extracts the latest observation year from the source header
   and column metadata, so no code changes are required for new release years.
