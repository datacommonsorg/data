# India_RBI_State_Statistics

## Import Overview

This import pipeline processes various socio-economic and agricultural statistics for Indian states, sourced from the Reserve Bank of India (RBI) Handbook of Statistics on Indian States. The data covers diverse categories including agriculture, environment, prices and wages, and infrastructure.

- **Source:** [Reserve Bank of India - Handbook of Statistics on Indian States](https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20States)
- **Description:** This dataset comprises state-wise statistical data for various indicators in India, as published by the Reserve Bank of India. The data is available in Excel (.xlsx) format.

## Configuration

The `rbi_download.py` script relies on a local, version-controlled JSON configuration file named `configs.json` to specify URLs, filenames, and categories for the data to be downloaded.

Sample structure of `configs.json`:
```json
{
  "URLS_CONFIG": [
    {
      "url": "https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/58T_xxxxxxxxxxxxx.XLSX",
      "category": "agriculture",
      "filename": "state_wise_pattern_of_land_use_gross_sown_area.xlsx"
    }
  ]
}
```

This makes the import process **Semi-Automated**: if download URLs change in future RBI releases (due to updated publication links or revised tables), only `configs.json` needs to be updated without modifying script logic. Additionally, `rbi_download.py` employs connection pooling with `requests.Session()` + `HTTPAdapter(Retry(...))`, validates file magic bytes (`PK\x03\x04`), and atomically writes downloaded files to prevent corrupted/partial files.

## Data Acquisition and Initial Preprocessing

The `rbi_download.py` script is responsible for both downloading the raw Excel data and performing an initial preprocessing step:
- **Cell Cleaning (`clean_cell`)**: Strips footnote markers (`*` and `@`), trims leading/trailing whitespace, and converts empty or literal `'nan'` strings to true `NaN` values so `stat_var_processor.py` does not emit malformed string observations.
- **Header Normalization (`safe_to_numeric`)**: Converts numeric or float-coerced year headers (e.g., `2015.0`, `'2016@'`) in `State/Union Territory` header rows to integers (`2015`, `2016`) so they match integer string keys in the PVMaps.

### How to Run:

Execute the `rbi_download.py` script. This script will:
1.  Automatically create an `input_files` directory if it doesn't exist.
2.  Download the necessary Excel files into subfolders within `input_files` (e.g., `input_files/agriculture/`), verifying `PK\x03\x04` ZIP signatures and writing files atomically.
3.  Process each downloaded Excel file across all sheets using `clean_cell` and `safe_to_numeric`.

### Download Command:

```bash
python3 rbi_download.py
```

Optional flag:
- `--config_file_path`: Path to the JSON config file (defaults to local `configs.json`; also supports a GCS URI such as `gs://<bucket>/configs.json`).

### Running Unit Tests:

To run the hermetic unit test suite for `rbi_download.py`:

```bash
python3 rbi_download_test.py
```

## Prerequisites

The following Python packages are required to run the download, preprocessing, and test suites:
- `pandas`
- `openpyxl`
- `requests`
- `google-cloud-storage`
- `absl-py`

Install dependencies via:
```bash
pip install pandas openpyxl requests google-cloud-storage absl-py
```

## Processing Section

The downloaded data is processed using the `stat_var_processor.py` script, which is part of the `/data/tools/statvar_importer/` toolkit. This script converts the raw Excel data into a structured format suitable for further analysis and ingestion. Each processing command specifies the input data file(s), the Property-Value (PV) map, the configuration file (metadata), a places resolver CSV, counter output CSV, and the desired output path.

### General Processing Command Structure:

```bash
python3 stat_var_processor.py \
    --input_data="<path_to_input_files>.xlsx" \
    --pv_map="<path_to_pv_map.csv>" \
    --config_file="<path_to_metadata.csv>" \
    --places_resolved_csv="<path_to_places_resolver.csv>" \
    --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" \
    --output_counters="<path_to_counters.csv>" \
    --output_path="<path_to_output_folder_and_filename_prefix>"
```

### How to Run Processing:

You can either execute the `run.sh` script or run each `stat_var_processor.py` command individually from the `/data/tools/statvar_importer/` directory.

#### Option 1: Using `run.sh`

```bash
sh run.sh
```

#### Option 2: Executing Individual Processing Commands

Navigate to the `/data/tools/statvar_importer/` directory before running the following commands, or adjust the relative paths accordingly. Note that wildcard `--input_data` paths must be enclosed in double quotes so `stat_var_processor.py` expands them internally.

### Processing Commands:

#### Agriculture Data:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/agriculture/*.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/agriculture_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/agriculture_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/agriculture/agriculture_output
```

#### Environment Data - State-wise Forest Cover:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_forest_cover.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_forest_cover_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_forest_cover_output
```

#### Environment Data - State-wise Tree Cover:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_tree_cover.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_tree_cover_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_tree_cover_output
```

#### Environment Data - Sub-division-wise Annual Rainfall:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/sub_division_wise_annual_rainfall.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/sub_division_wise_annual_rainfall_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/sub_division_wise_annual_rainfall_output
```

#### Environment Data - State-wise Expenditure on Relief from Natural Calamities:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_expenditure_on_relief_on_natural_calamities.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_expenditure_on_relief_on_natural_calamities_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_expenditure_on_relief_on_natural_calamities_output
```

#### Environment Data - State-wise Sustainable Development Goals (SDGs) Score:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_sustainable_development_goals_score_SDGs.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_sdg_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_sdg_score_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_sdg_score_output
```

#### Price and Wages Data:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/price_and_wages/*.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/price_wages_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/price_and_wages_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/price_and_wages/price_and_wages_output
```

#### Infrastructure Data - State-wise Per Capita Availability of Power:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_per_capita_availability_of_power.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_per_capita_availability_of_power_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_per_capita_availability_of_power_output
```

#### Infrastructure Data - State-wise Availability of Power:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_availability_of_power.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_availability_of_power_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_availability_of_power_output
```

#### Infrastructure Data - State-wise Installed Capacity of Power:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_installed_capacity_of_power.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_installed_capacity_of_power_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_installed_capacity_of_power_output
```

#### Infrastructure Data - State-wise Power Requirement:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_power_requirement.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_power_requirement_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_power_requirement_output
```

#### Infrastructure Data - State-wise Length of National Highways:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_length_of_national_highways.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_length_of_national_highways_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_length_of_national_highways_output
```

#### Infrastructure Data - State-wise Railway Route:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_railway_route.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_railway_route_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_railway_route_output
```

#### Infrastructure Data - State-wise Length of Roads:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_length_of_roads.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_length_of_roads_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_length_of_roads_output
```

#### Infrastructure Data - State-wise Length of State Highways:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_length_of_state_highways.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_length_of_state_highways_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_length_of_state_highways_output
```

#### Infrastructure Data - State-wise Electricity Transmission & Distribution Losses:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_electricity_transmission_distribution_losses.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_electricity_transmission_distribution_losses_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_electricity_transmission_distribution_losses_output
```

#### Infrastructure Data - State-wise Telephones per 100 Population:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_telephones_per_100_population.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_telephones_per_100_population_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_telephones_per_100_population_output
```

#### Infrastructure Data - State-wise Road Constructed under PMGSY:

```bash
python3 stat_var_processor.py \
    --input_data="../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_road_constructed_under_PMGSY.xlsx" \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_counters=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/counters/state_wise_road_constructed_under_pmgsy_counters.csv \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_road_constructed_under_pmgsy_output
```

## Validation Configuration and Thresholds

This import uses `validation_config.json` with:
1. **`DELETED_RECORDS_PERCENT: 7` (`check_deleted_records_percent`)**:
   - **Rationale & Analysis**: The threshold is set to `7%` to accommodate up to **6.94%** reported deletions across the 18 sub-imports (specifically **6.94%** in `sub_division_wise_annual_rainfall_output.csv`, **5.64%** in `agriculture_output.csv`, and **3.15%** in `state_wise_expenditure_on_relief_on_natural_calamities_output.csv`). These deletions are not data loss, but result from:
     1. **Place Resolution Corrections**: Remapping `"Haryana, Delhi & Chandigarh"` from `dcid:wikidataId/Q1174` (Haryana) to the dedicated IMD sub-division DCID `dcid:HaryanaDelhiChandigarh` (24 records / 6.94% in rainfall), and fixing `NCT of Delhi` from `wikidataId/Q1352` (erroneously Chennai) to `wikidataId/Q9357528` (439 records in agriculture, 13 records in relief expenditure).
     2. **Unit Schema Corrections**: Changing `Annual_Amount_FarmInventory_Fruits` in `agriculture_pvmap.csv` from `Hectare` to `MetricTon` (309 records in agriculture, where Import Differ classifies old unit nodes as deleted and new unit nodes as added).
     3. **Official RBI Source Revisions**: Retrospective updates by RBI to provisional figures for recent fiscal years (`2022-03` through `2024-03`) and UT consolidations (`Dadra & Nagar Haveli and Daman & Diu`).
   - **Justification Document**: For detailed root cause analysis, table breakdown, and justification, see the [RBI State Statistics Deletion Threshold Justification Doc](https://docs.google.com/document/d/1BLArT3T2-2EVql0Ol8tSYw9QtjFjzCzockJBquMC4AY/edit).
2. **`SQL_VALIDATOR` non-empty check (`check_expected_statvar_count`)**:
   - Asserts `statvar_cnt >= 1` so an empty `summary_report.csv` cannot vacuously pass grouped SQL queries.
3. **`SQL_VALIDATOR` cadence freshness check (`check_max_date_freshness`)**:
   - Asserts that each StatVar meets its expected RBI publication cadence (`2020`, `2022`, `2023`, or `2024`) with `WHERE MaxDate IS NOT NULL`.

## Refresh & Operational Maintenance

The import is configured with an automated cron schedule in `manifest.json`:
- **Schedule:** `0 10 * * 1` (Every Monday at 10:00 AM UTC).
- **Import Type:** Semi-Automated.

### Annual Refresh Procedure:
1. When the Reserve Bank of India publishes a new edition of the *Handbook of Statistics on Indian States*, check the [RBI Annual Publications Portal](https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20States).
2. If table download URLs have changed, update the `url` fields in `configs.json`.
3. If new tables, columns, or indicators are introduced, update the corresponding PVMap (`agriculture_pvmap.csv`, `environment_pvmap.csv`, `infrastructure_pvmap.csv`, or `price_wages_pvmap.csv`).
4. Re-run `python3 rbi_download.py` followed by `sh run.sh` to download and process the updated datasets.
5. Verify test outputs and pre-submit validation before raising a pull request.


