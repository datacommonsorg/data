# CDC WONDER - NNDSS Annual Summary (Infectious Diseases)

## Overview
This import processes annual summary data for Notifiable Infectious Diseases from CDC WONDER (National Notifiable Diseases Surveillance System). It contains incident counts of various infectious diseases reported across US states, territories, and regions, broken down by demographics and location (age, sex, race, ethnicity, region, and state).

- **Data Source:** [CDC WONDER NNDSS Annual Summary](https://wonder.cdc.gov/nndss-annual-summary.html) (Dataset Code: `D130`)
- **Temporal Coverage:** 2016–2023 (updated annually as new data is published)
- **Geographic Coverage:** US States, Territories, and Regions
- **Demographic Breakdowns:** Age, Sex, Race, Ethnicity, Region, Region/State
- **Statistical Variables:** Counts of reported cases for notifiable infectious diseases across various demographic and geographic aggregations.

---

## Data Acquisition & Refresh Strategy

### Refresh Mode
- **Mode:** Automatic
- **Schedule:** `0 0 1 7 *` (Runs annually on July 1st at 00:00 UTC)

### Acquisition Process
- Data is programmatically fetched from the CDC WONDER API endpoint (`https://wonder.cdc.gov/controller/datarequest/D130`) using `download_nndss_annual_data.py`.
- The script constructs XML request payloads for each breakdown and year, sends HTTP POST requests to the API, and enforces CDC WONDER rate limits (waiting $\ge$ 16 seconds between queries) with exponential retry backoff.
- The returned XML table responses are parsed and formatted into standard CSV files saved under `input_files/<breakdown>/NNDSS_Annual_Summary_Data_<year>.csv`.

---

## Directory Structure

- `download_nndss_annual_data.py`: Script to programmatically download CDC WONDER annual summary data via API for all breakdowns and years.
- `manifest.json`: Configuration for automated pipeline execution, scheduling, scripts, inputs, and validation rules.
- `validation_config.json`: Configuration defining validation rules (deleted records percent, golden file checks).
- `age_pvmap.csv`: Property-value mapping for age breakdowns.
- `race_region_sex_ethnicity_pvmap.csv`: Property-value mapping for race, sex, ethnicity, and region breakdowns.
- `region_state_pvmap.csv`: Property-value mapping for region and state breakdowns.
- `common_metadata.csv`: Shared metadata configuration file for `stat_var_processor.py`.
- `output.tmcf`: Template MCF mapping output CSV columns to Data Commons `StatVarObservation` nodes.
- `COPY`: GCS target path for unresolved MCF output (`unresolved_mcf/cdc/nndss_infectious_diseases_annual/latest`).
- `input_files/`: Raw annual input CSV files (2016–2023) organized in subdirectories by breakdown (`age/`, `ethnicity/`, `race/`, `region/`, `region_state/`, `sex/`).
- `golden_data/`: Contains golden files (`golden_summary_report.csv`, `golden_observations.csv`) for import validation.
- `test_data/`: Sample input files and expected outputs for processor validation and testing.
- `output/`: Processed output CSVs, TMCFs, and StatVar MCFs.

---

## Automated Execution (via Manifest)

The automated import is orchestrated via `manifest.json`. When executed by the Data Commons import pipeline, it automatically performs the following steps:

1. **Data Download:** Executes `download_nndss_annual_data.py` to fetch the latest raw data into `input_files/`.
2. **Data Processing:** Runs `stat_var_processor.py` across all 6 breakdown verticals (`race`, `region`, `sex`, `ethnicity`, `age`, `region_state`) using their respective property-value mappings and shared metadata:
   - `race`: `input_files/race/NNDSS_Annual_Summary_Data_*.csv` $\rightarrow$ `output/output_race`
   - `region`: `input_files/region/NNDSS_Annual_Summary_Data_*.csv` $\rightarrow$ `output/output_region`
   - `sex`: `input_files/sex/NNDSS_Annual_Summary_Data_*.csv` $\rightarrow$ `output/output_sex`
   - `ethnicity`: `input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv` $\rightarrow$ `output/output_ethnicity`
   - `age`: `input_files/age/NNDSS_Annual_Summary_Data_*.csv` $\rightarrow$ `output/output_age`
   - `region_state`: `input_files/region_state/NNDSS_Annual_Summary_Data_*.csv` $\rightarrow$ `output/output_region_state`
3. **Validation:** Executes automated validation checks against `validation_config.json`:
   - `check_deleted_records_percent`: Ensures deleted records do not exceed the 10% threshold.
   - `check_goldens_summary_report`: Validates the summary report against `golden_data/golden_summary_report.csv`.
   - `check_goldens_output_csv`: Validates generated observations against `golden_data/golden_observations.csv`.

---

## Manual Execution Instructions

### 1. Download Input Data
To manually download or refresh input CSVs from CDC WONDER:

**Download all breakdowns and years (2016–2023):**
```bash
python3 download_nndss_annual_data.py --verticals=all --years=all --output_dir=./input_files
```

**Download specific breakdowns or years:**
```bash
python3 download_nndss_annual_data.py --verticals=age,sex --years=2022,2023 --output_dir=./input_files
```

### 2. Process Data

#### Option A: Running from the Import Directory (matching `manifest.json`)
```bash
# Race Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/race/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=./output/output_race

# Region Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/region/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=./output/output_region

# Sex Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/sex/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=./output/output_sex

# Ethnicity Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=./output/output_ethnicity

# Age Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/age/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=age_pvmap.csv \
  --config_file=common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=./output/output_age

# Region/State Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/region_state/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=region_state_pvmap.csv \
  --config_file=common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=./output/output_region_state
```

#### Option B: Running from the Repository Root (`data/`)
```bash
# Age Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/age/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_age

# Race Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/race/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_race

# Region Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/region/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_region

# Sex Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/sex/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_sex

# Ethnicity Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_ethnicity

# Region/State Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/region_state/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/region_state_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_region_state
```

### 3. Testing with Sample Data
To test the processor using sample input data:
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/NNDSS_Annual_Summary_Data_2023.csv \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/test_output
```
