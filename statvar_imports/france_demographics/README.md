# France Demographics Data Import

This directory contains the scripts and configuration to import France demographics data from [INSEE](https://www.insee.fr/en/statistiques/8333211?sommaire=8333329).

## Data Source
- **Provider**: INSEE (Institut national de la statistique et des études économiques)
- **Description**: Population estimates, age structures, and demographic components.
- **URL**: [INSEE Population Statistics](https://www.insee.fr/en/statistiques/8333211?sommaire=8333329)

## Directory Structure
- `run.sh`: Primary entry point. Orchestrates downloading, renaming files, and processing.
- `*_pvmap.csv`: Property-Value mapping files for the statvar processor.
- `france_demographics_metadata.csv`: Metadata configuration for the import.
- `manifest.json`: Import specification for the automation pipeline.

## Usage

### 1. Automated Execution
To ensure the pipeline works consistently across local environments and Google Cloud Batch, use the run.sh script. This script handles the downloading of INSEE files, renames them to match expected configuration, and runs the stat_var_processor.

```chmod +x run.sh
./run.sh
```

### 2. Manual Processing
If you already have the data files downloaded and renamed in input_files/, you can run the `stat_var_processor.py` tool for each dataset to generate MCF and CSV files.

**Annual Population Components:**
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data='./input_files/annual_population_components.xlsx' \
  --pv_map='annual_population_components_pvmap.csv' \
  --config_file='france_demographics_metadata.csv' \
  --output_path='output/annual_population_components_output'
```

**Population by Sex and Detailed Age:**
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data='./input_files/population_sex_detailed_age.xlsx' \
  --pv_map='population_sex_detailed_age_pvmap.csv' \
  --config_file='france_demographics_metadata.csv' \
  --output_path='output/population_sex_detailed_age_output'
```

**Population by Sex and Age Groups:**
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data='./input_files/population_sex_age_groups.xlsx' \
  --pv_map='population_sex_age_groups_pvmap.csv' \
  --config_file='france_demographics_metadata.csv' \
  --output_path='output/population_sex_age_groups_output'
```

**Average and Median Age:**
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data='./input_files/average_median_age.xlsx' \
  --pv_map='average_median_age_pvmap.csv' \
  --config_file='france_demographics_metadata.csv' \
  --output_path='output/average_median_age_output'
```
