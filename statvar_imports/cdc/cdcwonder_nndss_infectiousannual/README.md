# CDC WONDER - NNDSS Annual Summary (Infectious Diseases)

## Overview
This import processes annual summary data for Notifiable Infectious Diseases from CDC WONDER (National Notifiable Diseases Surveillance System). It contains incident counts of various infectious diseases reported across US states, territories, and regions, broken down by demographics and location (age, sex, race, ethnicity, region, and state).

- **Data Source:** [CDC WONDER NNDSS Annual Summary](https://wonder.cdc.gov/nndss-annual-summary.html)
- **Temporal Coverage:** 2016–2023
- **Geographic Coverage:** US States, Territories, and Regions
- **Demographic Breakdowns:** Age, Sex, Race, Ethnicity, Region, Region/State

---

## Data Acquisition & Refresh Strategy

### Acquisition Process
- **Refresh Mode:** Semi-automatic.
- **Background & Analysis:**
  - Source data is interactively queried and exported from [CDC WONDER](https://wonder.cdc.gov/nndss-annual-summary.html).
  - Due to requiring Selenium/manual browser interactions to download data from CDC WONDER, this import is set up for semi-automatic refresh.

---


## Directory Structure

- `age_pvmap.csv`: Property-value mapping for age breakdowns.
- `race_region_sex_ethnicity_pvmap.csv`: Property-value mapping for race, region, sex, and ethnicity breakdowns.
- `region_state_pvmap.csv`: Property-value mapping for region and state breakdowns.
- `common_metadata.csv`: Shared metadata configuration file for `stat_var_processor.py`.
- `data/`: Raw annual input CSV files (2016–2023) organized in subdirectories by breakdown (`age/`, `ethnicity/`, `race/`, `region/`, `region_state/`, `sex/`).
- `test_data/`: Sample input and golden output files for validating processor runs.

---

## Processing Instructions

Run `stat_var_processor.py` from the root of the `data` repository:

**Age Breakdown:**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/data/age/*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output_age/output
```

**Race Breakdown:**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/data/race/*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output_race/output
```

**Region Breakdown:**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/data/region/*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output_region/output
```

**Sex Breakdown:**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/data/sex/*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output_sex/output
```

**Ethnicity Breakdown:**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/data/ethnicity/*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output_ethnicity/output
```

**Region State Breakdown:**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/data/region_state/*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/region_state_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output_region_state/output
```
