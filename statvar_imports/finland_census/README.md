# Finland Demographics Dataset
## Overview

This dataset contains demographic information from Finland sourced from Statistics Finland (Tilastokeskus). It provides comprehensive longitudinal coverage of Finland’s national demographics featuring annual data from 1990 to present date. The geographic scope is standardized according to the latest regional division, ensuring consistency across the time series despite historical administrative changes. It offers high-resolution granularity through 43 unique statistical metrics that encompass population growth, age distribution, linguistic diversity, religious affiliation and urban-rural classification. Data is reported in multiple units for versatile analysis, including absolute counts, percentages (%), and population density (persons/km²), allowing for both scale-based and proportional statistical modeling.

**type of place:** Country
**years:** 1990 to present date

## Data Source
**Source URL:**
https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__vaerak/11ra.px

## License
**License Type:** 
Creative Commons Attribution 4.0 International
**License URL:** 
https://creativecommons.org/licenses/by/4.0/
**License Description:**
The [Statistics Finland Terms of Use](https://stat.fi/en/about-us/get-to-know-statistics-finland/legislation/terms-of-use) state the following:
"Statistics Finland's open data materials and public content of the web service are covered by the Creative Commons Attribution 4.0 International licence. According to the licence, you can copy, edit and share these data either in original or edited format. You can also combine the data with other data and use the data for commercial purposes as well. This licence applies to texts, tables and statistical graphs."

## Refresh Type
Automatic Refresh

## Download & Processing Details:
- **Download (`data_download.py`)**: Fetches data dynamically from the Statistics Finland PxWeb API through the following steps:
  1. **Metadata Resolution**: Sends a GET request to the PxWeb table metadata endpoint to dynamically identify and map structural dimension codes for `Area`, `Information`, and `Year`.
  2. **POST Query Execution**: Constructs a JSON POST request payload querying the whole country (`SSS`) for all available metrics (`*`) and all historical years (`*`).
  3. **CSV Formatting**: Decodes the response bytes, prepends the dataset title rows to match the PV map layout, ensures the `input_files/` directory exists, and saves the formatted CSV locally.
- **Processing (`stat_var_processor.py`)**: Maps the raw input CSV to Data Commons StatVarObservations and Template MCF using `finland_census_pvmap.csv` and `finland_census_metadata.csv`.

For Test Data Run

```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./test_data/finland_census_input.csv" \
  "--pv_map=./finland_census_pvmap.csv" \
  "--output_path=./test_data/finland_census_output" \
  "--config_file=./finland_census_metadata.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

## Key Files
- `data_download.py`: Downloads the data from Finland's official database, formats it, and saves it to input_files directory
- `finland_census_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `finland_census_metadata.csv`: Configuration parameters for the processor.
- `output_files/finland_census_output.csv`: Processed statistical observations.
- `output_files/finland_census_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.
    
## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint output_files/*.csv 
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/finland_census_input.csv`
- Expected Output: `test_data/finland_census_output.csv`
- Expected TMCF: `test_data/finland_census_output.tmcf`
