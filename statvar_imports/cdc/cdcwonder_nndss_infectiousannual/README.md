# CDC WONDER - NNDSS Annual Summary (Infectious Diseases)

## Overview
This import processes annual summary data for Notifiable Infectious Diseases from CDC WONDER (National Notifiable Diseases Surveillance System). It contains incident counts of various infectious diseases reported across US states, territories, and regions, broken down by demographics and location (age, sex, race, ethnicity, region, and state).

- **Data Source:** [CDC WONDER NNDSS Annual Summary](https://wonder.cdc.gov/nndss-annual-summary.html) (Dataset Code: `D130`)
- **Temporal Coverage:** 2016–2023 (updated annually as new data is published; auto-computed dynamically for annual refreshes)
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
- The script constructs XML request payloads for each breakdown and year, sends HTTP POST requests using a persistent `requests.Session` with connection pooling, and enforces CDC WONDER rate limits (waiting >= 16 seconds between queries) with exponential retry backoff on errors and rate limit responses.
- Atomic file writes via temporary files (`tempfile.NamedTemporaryFile` + `os.replace`) ensure no corrupted or partially written CSVs on interruption.
- The returned XML table responses are parsed and formatted into standard CSV files saved under `input_files/<breakdown>/NNDSS_Annual_Summary_Data_<year>.csv`.

---

## Directory Structure

- `download_nndss_annual_data.py`: Script to programmatically download CDC WONDER annual summary data via API for all breakdowns and years.
- `download_nndss_annual_data_test.py`: Unit tests for CDC WONDER downloader, XML generation, table parsing, error handling, rate limiting retry backoff, and atomic file writes.
- `manifest.json`: Configuration for automated pipeline execution, scheduling, scripts, inputs, source files, and validation rules.
- `validation_config.json`: Configuration defining validation rules (deleted records percent, golden file checks).
- `age_pvmap.csv`: Property-value mapping for age breakdowns.
- `race_sex_ethnicity_pvmap.csv`: Property-value mapping for race, sex, and ethnicity breakdowns.
- `region_pvmap.csv`: Property-value mapping for region breakdowns.
- `region_state_pvmap.csv`: Property-value mapping for region and state breakdowns.
- `common_metadata.csv`: Shared metadata configuration file for `stat_var_processor.py`.
- `output.tmcf`: Template MCF mapping output CSV columns to Data Commons `StatVarObservation` nodes.
- `COPY`: GCS target path for unresolved MCF output (`unresolved_mcf/cdc/nndss_infectious_diseases_annual/latest`).
- `input_files/`: Raw annual input CSV files (2016–2023) organized in subdirectories by breakdown (`age/`, `ethnicity/`, `race/`, `region/`, `region_state/`, `sex/`).
- `golden_data/`: Contains golden files (`golden_summary_report.csv`, `golden_observations.csv`) for import validation.
- `test_data/`: Sample input files and expected outputs across all 6 verticals (`age/`, `ethnicity/`, `race/`, `region/`, `region_state/`, `sex/`) for processor validation and testing.
- `output/`: Processed output CSVs (`output_*.csv`), TMCFs (`output_*.tmcf`), and StatVar Node MCFs (`output_*.mcf`).
- `counters/`: Generated summary counters CSV files (`<vertical>_output_counters.csv`) produced by `stat_var_processor.py`.

---

## Automated Execution (via Manifest)

The automated import is orchestrated via `manifest.json`. When executed by the Data Commons import pipeline, it automatically performs the following steps:

1. **Data Download:** Executes `download_nndss_annual_data.py` to fetch the latest raw data into `input_files/`.
2. **Data Processing:** Runs `stat_var_processor.py` across all 6 breakdown verticals (`race`, `region`, `sex`, `ethnicity`, `age`, `region_state`) using their respective property-value mappings, shared metadata, and writes output counters:
   - `race`: `input_files/race/NNDSS_Annual_Summary_Data_*.csv` -> `output/output_race`, counters: `counters/race_output_counters.csv`
   - `region`: `input_files/region/NNDSS_Annual_Summary_Data_*.csv` -> `output/output_region`, counters: `counters/region_output_counters.csv`
   - `sex`: `input_files/sex/NNDSS_Annual_Summary_Data_*.csv` -> `output/output_sex`, counters: `counters/sex_output_counters.csv`
   - `ethnicity`: `input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv` -> `output/output_ethnicity`, counters: `counters/ethnicity_output_counters.csv`
   - `age`: `input_files/age/NNDSS_Annual_Summary_Data_*.csv` -> `output/output_age`, counters: `counters/age_output_counters.csv`
   - `region_state`: `input_files/region_state/NNDSS_Annual_Summary_Data_*.csv` -> `output/output_region_state`, counters: `counters/region_state_output_counters.csv`
3. **Import Inputs & Retained Outputs:**
   - Template MCF: `output/output_age.tmcf`
   - Cleaned CSV: `output/output_*.csv`
   - Node MCF: `output/output_*.mcf`
4. **Source Files & Retained Artifacts:**
   - `./input_files/*/NNDSS_Annual_Summary_Data_*.csv`
   - `golden_data/*.csv`
   - `counters/*.csv`
5. **Validation:** Executes automated validation checks against `validation_config.json`:
   - `check_deleted_records_percent`: Ensures deleted records do not exceed the 0.1% threshold.
   - `check_goldens_summary_report`: Validates the summary report against `golden_data/golden_summary_report.csv`.
   - `check_goldens_output_csv`: Validates generated observations against `golden_data/golden_observations.csv`.

---

## Manual Execution Instructions

### 1. Download Input Data
To manually download or refresh input CSVs from CDC WONDER:

**Download all breakdowns and years (2016 through available):**
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
  --pv_map=race_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_race \
  --output_counters=counters/race_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/region/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=region_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_region \
  --output_counters=counters/region_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Sex Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/sex/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_sex \
  --output_counters=counters/sex_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Ethnicity Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_sex_ethnicity_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_ethnicity \
  --output_counters=counters/ethnicity_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Age Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/age/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=age_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_age \
  --output_counters=counters/age_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region/State Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/region_state/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=region_state_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_region_state \
  --output_counters=counters/region_state_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

#### Option B: Running from the Repository Root (`data/`)
```bash
# Race Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/race/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_race \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/race_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/region/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/region_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_region \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/region_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Sex Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/sex/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_sex \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/sex_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Ethnicity Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_sex_ethnicity_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_ethnicity \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/ethnicity_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Age Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/age/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_age \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/age_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region/State Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/region_state/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/region_state_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_region_state \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/region_state_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

### 3. Testing with Sample Data
To test the processor using sample input data for any breakdown vertical:
```bash
# Test Age Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/NNDSS_Annual_Summary_Data_2023.csv \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/test_output \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/test_counters.csv
```

### 4. Running Downloader Unit Tests
To run unit tests for the CDC WONDER downloader (verifying XML generation, table parsing, error handling, rate limiting retry backoff, and atomic file writes):

**From repository root (`data/`):**
```bash
python3 -m unittest statvar_imports/cdc/cdcwonder_nndss_infectiousannual/download_nndss_annual_data_test.py
```

**From import directory (`statvar_imports/cdc/cdcwonder_nndss_infectiousannual/`):**
```bash
python3 -m unittest download_nndss_annual_data_test.py
```
