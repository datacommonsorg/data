# Statistics Denmark Demographics Dataset
## Overview
This dataset contains demographic statistics for the population of Denmark, sourced from Statistics Denmark. It includes two primary datasets covering quarterly and annual population breakdowns across various dimensions like geography (regions and municipalities), sex, age, and marital status.

The import covers:
- **Population (Quarterly):** Population count by region, marital status, age, and sex at the first day of each quarter (Table FOLK1A).
- **Population (Annual):** Population count by sex and age groups.

Type of place: Country
Includes Denmark, Regions (NUTS2), and Municipalities.

## Data Source
**Source URL:**
- Main Portal: https://www.statbank.dk/statbank5a/default.asp?w=1396
- Specific Table (FOLK1A): https://www.statbank.dk/FOLK1A

**Provenance Description:**
The data is provided by Statistics Denmark, the central authority for Danish statistics. The population figures are derived from the Central Person Register (CPR) and reflect the population residing in Denmark on the first day of the period.

## How To Download Input Data
To download the data manually:
1. Go to the [StatBank Denmark Portal](https://www.statbank.dk/statbank5a/default.asp?w=1396).
2. Browse or search for the desired population tables. For quarterly demographics, search for table **FOLK1A** (Population at the first day of the quarter).
3. Select the desired variables:
   - **Region:** All Denmark, regions, or municipalities.
   - **Marital Status:** Never married, Married/separated, Widowed, Divorced.
   - **Age:** Individual ages or age groups.
   - **Sex:** Men, Women.
   - **Time:** Quarters.
4. Click "Show table" and then "Download" to save as CSV.

## Processing Instructions
To process the Denmark Demographics data and generate statistical variables, use the following command:

**For Data Run (Quarterly Run)**
```python ../../tools/statvar_importer/stat_var_processor.py \
    --input_data='gs://unresolved_mcf/country/denmark/input_files/population_quarterly_region_time_marital_status_input.csv' \
    --pv_map='population_quartely_region_time_marital_status_pvmap.csv' \
    --output_path='population_quartely_region_time_marital_status_output' \
    --config_file='denmark_demographics_metadata.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```
**For Data Run (Annual Run)**
```python ../../tools/statvar_importer/stat_var_processor.py \
    --input_data='gs://unresolved_mcf/country/denmark/input_files/population_sex_age_time_input.csv' \
    --pv_map='population_sex_age_time_pvmap.csv' \
    --output_path='population_sex_age_time_output' \
    --config_file='denmark_demographics_metadata.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

This generates the following output files for the first time run:
- output.csv
- output_stat_vars_schema.mcf
- output_stat_vars.mcf
- output.tmcf

## Data Quality Checks and Validation
Validation is performed using the Data Commons import tool:

```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar lint \
    output_stat_vars_schema.mcf \
    output.csv \
    output.tmcf \
    output_stat_vars.mcf  
```

The tool generates a `report.json`, `summary_report.csv`, and `summary_report.html` which can be used to identify errors or warnings in the generated data.
