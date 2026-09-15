# CDC WONDER - NNDSS Annual Summary (Infectious Diseases)

## Overview
This import processes annual summary data for Notifiable Infectious Diseases from CDC WONDER (National Notifiable Diseases Surveillance System). It contains incident counts of various infectious diseases reported across US states, territories, and regions, broken down by demographics and location (age, sex, race, ethnicity, region, and region/state).

- **Data Source:** [CDC WONDER NNDSS Annual Summary](https://wonder.cdc.gov/nndss-annual-summary.html) (Dataset Code: `D130`)
- **Temporal Coverage:** 2016–present (currently 2016–2023 published; dynamically discovered up to `current_year - 1`)
- **Geographic Coverage:** US States, Territories, and Regions (50 States, District of Columbia, New York City, and US territories including Puerto Rico, Guam, US Virgin Islands, American Samoa, and Northern Mariana Islands)
- **Demographic Breakdowns:** Age, Sex, Race, Ethnicity, Region, Region/State
- **Statistical Variables:** Incident case counts (`MedicalConditionIncident`) for notifiable infectious diseases across various demographic and geographic aggregations, measured over 1-year observation periods (`P1Y`).

---

## Data Acquisition & Refresh Strategy

### Refresh Mode
- **Mode:** Automatic
- **Schedule:** `0 0 15 * *` (Runs monthly on the 15th at 00:00 UTC to detect new annual summaries as published)

### Acquisition Process
- Data is programmatically fetched from the CDC WONDER API endpoint (`https://wonder.cdc.gov/controller/datarequest/D130`) using `download_nndss_annual_data.py`.
- Built with Google `absl` framework (`absl.app`, `absl.flags`, and `absl.logging`), accepting flags `--verticals`, `--years`, and `--output_dir`.
- The script constructs vertical-specific XML request payloads for each breakdown and year, sends HTTP POST requests using a persistent `requests.Session` with connection pooling, and enforces CDC WONDER rate limits (waiting >= 16 seconds between queries) with exponential retry backoff on server errors and rate limit responses.
- **Dynamic Year Probing & Graceful Early Exit:** Default `--years=all` probes years chronologically from 2016 up to `datetime.date.today().year - 1`. If CDC WONDER signals that a year is not yet released (`YearUnavailableError`), the script logs an informative warning, skips the unreleased year, terminates further year probes for that vertical, and skips that year across remaining verticals without failing the pipeline.
- **Atomic File Writes:** Output CSVs are written to temporary files (`tempfile.NamedTemporaryFile` + `os.replace`), guaranteeing that partially downloaded or interrupted files are never exposed as successful downloads.
- Raw CSV files are saved under `input_files/<breakdown>/NNDSS_Annual_Summary_Data_<year>.csv`.

---

## Directory Structure

- `download_nndss_annual_data.py`: Script using `absl` to programmatically download CDC WONDER annual summary data via API for all breakdowns and years with dynamic year detection and rate limiting.
- `download_nndss_annual_data_test.py`: Comprehensive unit tests verifying XML payload generation, table parsing, error handling, rate limiting retry backoff, dynamic year availability detection, absl flags/app execution, and atomic file writes.
- `manifest.json`: Configuration for automated pipeline execution, scheduling (`0 0 15 * *`), scripts, inputs, source files, and validation rules.
- `validation_config.json`: Configuration defining automated validation rules (deleted records percent threshold, golden summary report checks, golden observations checks).
- `diseases_pvmap.csv`: Modular property-value mapping defining disease codes (`Disease Code:<ID>`) mapped to Data Commons medical conditions (`medicalCondition`), medical statuses (`medicalStatus`), serotypes (`serotype`), serogroups (`serogroup`), and treatment methods (`treatmentMethod`), shared across all verticals.
- `race_region_sex_ethnicity_pvmap.csv`: Standardized property-value mapping for race, region, sex, and ethnicity demographic breakdowns with prefixed keys (`Sex Code:<ID>`, `Race Code:<ID>`, `Ethnicity Code:<ID>`, `Regions Code:<ID>`) and age <= 5 disease overrides.
- `age_pvmap.csv`: Property-value mapping for age breakdowns (`Age Code:<ID>`) and age <= 5 disease overrides.
- `region_state_pvmap.csv`: Property-value mapping for geographic region and state breakdowns (`Regions/States Code:<ID>`) and age <= 5 disease overrides.
- `common_metadata.csv`: Shared metadata configuration file for `stat_var_processor.py`.
- `input_files/`: Raw annual input CSV files (2016–2023) organized in subdirectories by breakdown (`age/`, `ethnicity/`, `race/`, `region/`, `region_state/`, `sex/`).
- `golden_data/`: Contains golden files (`golden_summary_report.csv`, `golden_observations.csv`) for import validation.
- `test_data/`: Sample input files (`NNDSS_Annual_Summary_Data_2023.csv`) and expected outputs (`output.csv`) across all 6 verticals (`age/`, `ethnicity/`, `race/`, `region/`, `region_state/`, `sex/`) for processor validation and fast local testing.
- `output/`: Processed output CSVs (`output_*.csv`), TMCFs (`output_*.tmcf`), and StatVar Node MCFs (`output_*.mcf`).
- `counters/`: Generated summary counters CSV files (`<vertical>_output_counters.csv`) produced by `stat_var_processor.py`.

---

## Property-Value Mapping (PV Map) Architecture

The import uses a modular PV map design to maintain separation of concerns, eliminate code duplication, and avoid ambiguous key mappings:

1. **Modular Disease Definitions (`diseases_pvmap.csv`):**
   - Serves as the single shared source of truth for disease code mappings across all breakdown verticals.
   - Maps CDC WONDER `Disease Code` values to Data Commons `medicalCondition` DCIDs (e.g., `HaemophilusInfluenzae__InvasiveDisease`, `StreptococcusPneumonia`, `Salmonellosis`, `ZikaVirusDisease`), along with specific medical statuses (`ConfirmedCase`, `ProbableCase`), serotypes (`SerotypeB`, `NonSerotypeB`), and serogroups.

2. **Column-Prefixed Mapping Keys:**
   - To prevent collisions across columns with numeric codes, all mapping keys include explicit column prefixes matching the CDC WONDER CSV headers:
     - `Disease Code:<ID>` in `diseases_pvmap.csv`
     - `Age Code:<ID>` in `age_pvmap.csv`
     - `Sex Code:<ID>`, `Race Code:<ID>`, `Ethnicity Code:<ID>`, `Regions Code:<ID>` in `race_region_sex_ethnicity_pvmap.csv`
     - `Regions/States Code:<ID>` in `region_state_pvmap.csv`
   - Suppressed or unmapped values (e.g., code `98` for suppressed cells, unsupported place groupings) are explicitly ignored with meaningful `#ignore` reasons (`suppressed data`, `unsupported place grouping`).

3. **Multi-PVMap Composition:**
   - `stat_var_processor.py` natively supports comma-separated PV map files via `--pv_map`.
   - Each vertical invocation combines its specific dimension mapping with `diseases_pvmap.csv` (e.g., `--pv_map=age_pvmap.csv,diseases_pvmap.csv`).

---

## Automated Execution (via Manifest)

The automated import is orchestrated via `manifest.json`. When executed by the Data Commons import pipeline, it automatically performs the following steps:

1. **Data Download:** Executes `download_nndss_annual_data.py` to fetch raw data into `input_files/`.
2. **Data Processing:** Runs `stat_var_processor.py` across all 6 breakdown verticals (`race`, `region`, `sex`, `ethnicity`, `age`, `region_state`) using their respective modularized property-value mappings (combined with `diseases_pvmap.csv`), shared metadata, and writes output counters:
   - `race`: `input_files/race/NNDSS_Annual_Summary_Data_*.csv` (pvmap: `race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv`) -> `output/output_race`, counters: `counters/race_output_counters.csv`
   - `region`: `input_files/region/NNDSS_Annual_Summary_Data_*.csv` (pvmap: `race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv`) -> `output/output_region`, counters: `counters/region_output_counters.csv`
   - `sex`: `input_files/sex/NNDSS_Annual_Summary_Data_*.csv` (pvmap: `race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv`) -> `output/output_sex`, counters: `counters/sex_output_counters.csv`
   - `ethnicity`: `input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv` (pvmap: `race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv`) -> `output/output_ethnicity`, counters: `counters/ethnicity_output_counters.csv`
   - `age`: `input_files/age/NNDSS_Annual_Summary_Data_*.csv` (pvmap: `age_pvmap.csv,diseases_pvmap.csv`) -> `output/output_age`, counters: `counters/age_output_counters.csv`
   - `region_state`: `input_files/region_state/NNDSS_Annual_Summary_Data_*.csv` (pvmap: `region_state_pvmap.csv,diseases_pvmap.csv`) -> `output/output_region_state`, counters: `counters/region_state_output_counters.csv`
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
  --pv_map=race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_race \
  --output_counters=counters/race_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/region/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_region \
  --output_counters=counters/region_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Sex Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/sex/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_sex \
  --output_counters=counters/sex_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Ethnicity Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_ethnicity \
  --output_counters=counters/ethnicity_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Age Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/age/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=age_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./output/output_age \
  --output_counters=counters/age_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region/State Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="./input_files/region_state/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=region_state_pvmap.csv,diseases_pvmap.csv \
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
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_race \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/race_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/region/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_region \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/region_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Sex Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/sex/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_sex \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/sex_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Ethnicity Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/ethnicity/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_ethnicity \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/ethnicity_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Age Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/age/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_age \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/age_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Region/State Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/cdc/cdcwonder_nndss_infectiousannual/input_files/region_state/NNDSS_Annual_Summary_Data_*.csv" \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/region_state_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/output/output_region_state \
  --output_counters=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/counters/region_state_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

### 3. Testing with Sample Data
To test the processor using sample input data for any breakdown vertical:

**From import directory (`statvar_imports/cdc/cdcwonder_nndss_infectiousannual/`):**
```bash
# Test Age Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=./test_data/age/NNDSS_Annual_Summary_Data_*.csv \
  --pv_map=age_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./test_data/age/output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Test Race / Region / Sex / Ethnicity Breakdown (e.g., Race)
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=./test_data/race/NNDSS_Annual_Summary_Data_*.csv \
  --pv_map=race_region_sex_ethnicity_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./test_data/race/output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Test Region/State Breakdown
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=./test_data/region_state/NNDSS_Annual_Summary_Data_*.csv \
  --pv_map=region_state_pvmap.csv,diseases_pvmap.csv \
  --config_file=common_metadata.csv \
  --output_path=./test_data/region_state/output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

**From repository root (`data/`):**
```bash
# Test Age Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/NNDSS_Annual_Summary_Data_2023.csv \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/age_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/age/output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Test Race / Region / Sex / Ethnicity Breakdown (e.g., Race)
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/race/NNDSS_Annual_Summary_Data_2023.csv \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/race_region_sex_ethnicity_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/race/output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Test Region/State Breakdown
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/region_state/NNDSS_Annual_Summary_Data_2023.csv \
  --pv_map=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/region_state_pvmap.csv,statvar_imports/cdc/cdcwonder_nndss_infectiousannual/diseases_pvmap.csv \
  --config_file=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/common_metadata.csv \
  --output_path=statvar_imports/cdc/cdcwonder_nndss_infectiousannual/test_data/region_state/output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

### 4. Running Downloader Unit Tests
To run unit tests for the CDC WONDER downloader (verifying XML generation, table parsing, error handling, rate limiting retry backoff, dynamic year availability detection, absl flags/app execution, and atomic file writes):

**From repository root (`data/`):**
```bash
python3 -m unittest statvar_imports/cdc/cdcwonder_nndss_infectiousannual/download_nndss_annual_data_test.py
```

**From import directory (`statvar_imports/cdc/cdcwonder_nndss_infectiousannual/`):**
```bash
python3 -m unittest download_nndss_annual_data_test.py
```
