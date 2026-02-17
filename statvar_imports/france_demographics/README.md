# France Demographics Data Import

This directory contains the scripts and configuration to import France demographics data from [INSEE](https://www.insee.fr/en/statistiques/8333211?sommaire=8333329).

## Data Source
- **Provider**: INSEE (Institut national de la statistique et des études économiques)
- **Description**: Population estimates, age structures, and demographic components.
- **URL**: [INSEE Population Statistics](https://www.insee.fr/en/statistiques/8333211?sommaire=8333329)

## Directory Structure
- `download_input_data.py`: Script to download source Excel files from INSEE.
- `*_pvmap.csv`: Property-Value mapping files for the statvar processor.
- `france_demographics_metadata.csv`: Metadata configuration for the import.
- `manifest.json`: Import specification.

## Usage

### 1. Download Data
Run the download script to fetch the latest data files into `input_files/`.

```bash
python3 download_input_data.py
```

### 2. Process Data
Run the `stat_var_processor.py` tool for each dataset to generate MCF and CSV files.

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
