
# India_RBI_State_Statistics

## Import Overview

This import pipeline processes various socio-economic and agricultural statistics for Indian states, sourced from the Reserve Bank of India (RBI) Handbook of Statistics on Indian States. The data covers diverse categories including agriculture, environment, prices and wages, and infrastructure.

- **Source:** [Reserve Bank of India - Handbook of Statistics on Indian States](https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20States)
- **Description:** This dataset comprises state-wise statistical data for various indicators in India, as published by the Reserve Bank of India. The data is available in Excel (.xlsx) format.

## Configuration

The `rbi_download.py` script relies on a configuration file named `configs.py` to fetch the URLs, filenames, and categories for the data to be downloaded. 

Sample data of the config file:
URLS_CONFIG=[
    {
        "url": "https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/58T_xxxxxxxxxxxxx.XLSX",
        "category": "agriculture",
        "filename": "state_wise_pattern_of_land_use_gross_sown_area.xlsx"
    },
    ...
    ]

This approach makes the import process semi-automatic: if the download URLs change in future RBI releases (which commonly happens due to shifting table numbers or publication structures), only this configuration file needs to be updated, rather than modifying the Python script itself.

## Data Acquisition and Initial Preprocessing

The `rbi_download.py` script is responsible for both downloading the raw Excel data and performing an initial preprocessing step. This preprocessing involves reading all sheets from the downloaded `.xlsx` files and replacing any `*` symbols with empty values.

### How to Run:

Execute the `rbi_download.py` script. This script will:
1.  Automatically create an `input_files` directory if it doesn't exist.
2.  Download the necessary Excel files into subfolders within `input_files` (e.g., `input_files/agriculture/`).
3.  Process each downloaded Excel file by reading all its sheets and replacing `*` characters with empty strings in all cells.

### Download Command:

```bash
python3 rbi_download.py
```

## Processing Section

The downloaded data is processed using the `stat_var_processor.py` script, which is part of the `/data/tools/statvar_importer/` toolkit. This script converts the raw Excel data into a structured format suitable for further analysis and ingestion. Each processing command specifies the input data file(s), the Property-Value (PV) map, the configuration file (metadata), a places resolver CSV, and the desired output path.

### General Processing Command Structure:

```bash
python3 stat_var_processor.py \
    --input_data='<path_to_input_files>.xlsx' \
    --pv_map='<path_to_pv_map.csv>' \
    --config_file='<path_to_metadata.csv>' \
    --places_resolved_csv='<path_to_places_resolver.csv>' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path='<path_to_output_folder_and_filename_prefix>'
```

### How to Run Processing:

You can either execute the `run.sh` script or run each `stat_var_processor.py` command individually from the `/data/tools/statvar_importer/` directory.

#### Option 1: Using `run.sh`

```bash
sh run.sh
```

#### Option 2: Executing Individual Processing Commands

Navigate to the `/data/tools/statvar_importer/` directory before running the following commands, or adjust the relative paths accordingly.

### Processing Commands:

#### Agriculture Data:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/agriculture/*.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/agriculture_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/agriculture/agriculture_output
```

#### Environment Data - State-wise Forest Cover:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_forest_cover.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_forest_cover_output
```

#### Environment Data - State-wise Tree Cover:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_tree_cover.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_tree_cover_output
```

#### Environment Data - Sub-division-wise Annual Rainfall:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/sub_division_wise_annual_rainfall.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/sub_division_wise_annual_rainfall_output
```

#### Environment Data - State-wise Expenditure on Relief from Natural Calamities:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_expenditure_on_relief_on_natural_calamities.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_expenditure_on_relief_on_natural_calamities_output
```

#### Environment Data - State-wise Sustainable Development Goals (SDGs) Score:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/environment/state_wise_sustainable_development_goals_score_SDGs.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/environment_sdg_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/environment/state_wise_sdg_score_output
```

#### Price and Wages Data:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/price_and_wages/*.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/price_wages_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/price_and_wages/price_and_wages_output
```

#### Infrastructure Data - State-wise Per Capita Availability of Power:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_per_capita_availability_of_power.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_per_capita_availability_of_power_output
```

#### Infrastructure Data - State-wise Availability of Power:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_availability_of_power.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_availability_of_power_output
```

#### Infrastructure Data - State-wise Installed Capacity of Power:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_installed_capacity_of_power.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_installed_capacity_of_power_output
```

#### Infrastructure Data - State-wise Power Requirement:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_power_requirement.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_power_requirement_output
```

#### Infrastructure Data - State-wise Length of National Highways:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_length_of_national_highways.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_length_of_national_highways_output
```

#### Infrastructure Data - State-wise Railway Route:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_railway_route.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_railway_route_output
```

#### Infrastructure Data - State-wise Length of Roads:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_length_of_roads.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_length_of_roads_output
```

#### Infrastructure Data - State-wise Length of State Highways:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_length_of_state_highways.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_length_of_state_highways_output
```

#### Infrastructure Data - State-wise Electricity Transmission & Distribution Losses:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_electricity_transmission_distribution_losses.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_electricity_transmission_distribution_losses_output
```

#### Infrastructure Data - State-wise Telephones per 100 Population:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_telephones_per_100_population.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_telephones_per_100_population_output
```

#### Infrastructure Data - State-wise Road Constructed under PMGSY:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/input_files/infrastructure/state_wise_road_constructed_under_PMGSY.xlsx \
    --pv_map=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/infrastructure_pvmap.csv \
    --config_file=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_metadata.csv \
    --places_resolved_csv=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_places_resolver.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/database_on_indian_economy/india_rbi_state_statistics/output_files/infrastructure/state_wise_road_constructed_under_pmgsy_output
```
