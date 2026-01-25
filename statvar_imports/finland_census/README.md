# Finland Demographics Dataset
## Overview

This dataset contains demographic information from Finland sourced from Statistics Finland (Tilastokeskus). This dataset provides comprehensive longitudinal coverage of Finland’s national demographics over a 34-year span, featuring annual data from 1990 to 2024. The geographic scope is standardized according to the January 1, 2025 regional division, ensuring consistency across the time series despite historical administrative changes. It offers high-resolution granularity through 43 unique statistical metrics that encompass population growth, age distribution, linguistic diversity, religious affiliation and urban-rural classification. Data is reported in multiple units for versatile analysis, including absolute counts, percentages (%), and population density (persons/km²), allowing for both scale-based and proportional statistical modeling.

## Data Acquisition

To download the latest version of this data or refresh the dataset for new years:

1. Navigate to the source: https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__vaerak/statfin_vaerak_pxt_11ra.px/table/tableViewLayout1/

2. Selection Criteria:
    - Area: Select WHOLE COUNTRY (or all individual municipalities for more granularity).
    - Information: Select all variables (Population, Language, Religion, Urban/Rural, etc.).
    - Year: Select the full range from 1990 to the most recent year.

3. Show and Save table Format: Choose "CSV (comma delimited)".

## Processing Instructions

To process the Finland Census data and generate statistical variables, use the following command from the "data" directory:

```bash
python ./data/tools/statvar_importer/stat_var_processor.py --input_data="./test_data/Finland_Census_input.csv" --pv_map=Finland_Census_pvmap.csv --config_file=Finland_Census_metadata.csv --output_path=Finland_Census_output

## Data Refresh & Maintenance

When Statistics Finland releases new annual updates (typically in the Spring), follow these steps:

1. Execute the Data Acquisition steps to get the latest CSV.

2. Check if new demographic categories were added. Update finland_census_pvmap.csv if new labels appear in the source.

3. The source uses . to represent unavailable data (e.g., Economic dependency ratio for the current year). The processor is configured to skip these entries during import.

4. Because the source applies the 2025 regional division retrospectively, check for municipal merger updates if downloading municipality-level data.

5. Ensure total population counts match the previous year's trend to verify no rows were dropped.

6. Execute the data processing step.
