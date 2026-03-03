# Canada Annual Population Estimates

## Overview

This dataset contains annual population estimates for Canada, its provinces, and territories, sourced from Statistics Canada. It provides a comprehensive demographic overview from 1971 to the present, broken down by age and gender.

The dataset features:
- **Geographic Coverage:** Canada (national), provinces, and territories.
- **Temporal Coverage:** Annual estimates (July 1st) from 1971 to the most recent year.
- **Granularity:**
    - **Age:** Single years of age (0 to 100+) and age groups.
    - **Gender:** Total, Men+, Women+.
- **Metrics:** Population counts (Persons).

This data is crucial for understanding demographic trends, population aging, and regional growth patterns across Canada.

## Data Acquisition

To download the latest version of this data or refresh the dataset:

1. **Navigate to the source:** [Table 17-10-0005-01: Population estimates on July 1st, by age and sex](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000501)

2. **Selection Criteria:**
    - **Geography:** Select "Canada" and all provinces/territories.
    - **Age group:** Select "All ages", individual years (0 to 100+), and standard age groups.
    - **Sex:** Select "Total - sex", "Males", "Females".
    - **Reference period:** Select from 1971 to the latest available year.

3. **Download:**
    - Select "Download options".
    - Choose "CSV (comma delimited)" to get the standard dataset file.
    - Save the file as `canada_annual_population_age_gender_input.csv` in the `gs://unresolved_mcf/country/canada_statistics_age_gender/input_files/` directory.

## Processing Instructions

To process the Canada Statistics data and generate statistical variables, use the following command from the repository root (or adjust paths relative to your current working directory):

```python ./data/tools/statvar_importer/stat_var_processor.py 
  --input_data="gs://unresolved_mcf/country/canada_statistics_age_gender/input_files/*.csv"
  --pv_map="./data/statvar_imports/canada_statistics/CanadaStatisticsAgeGender/canada_annual_population_age_gender_pvmap.csv" 
  --config_file="./data/statvar_imports/canada_statistics/CanadaStatisticsAgeGender/canada_annual_population_age_gender_metadata.csv" 
  --output_path="output/canada_annual_population_age_gender_output"
```

## Data Refresh & Maintenance

When Statistics Canada releases new annual updates (typically in late September):

1. **Execute the Data Acquisition steps** to get the latest CSV.

2. **Verify Column Names:** Check if Statistics Canada has changed any column names or codes (e.g., updates to "Gender" terminology). Update `canada_annual_population_age_gender_pvmap.csv` if necessary.

3. **Check for New Geographies:** Ensure no new administrative regions have been added or codes changed.

4. **Execute the processing step** to generate the new output files.
