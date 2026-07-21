# Finland Demographics Dataset
## Overview

This dataset contains demographic information from Finland sourced from Statistics Finland (Tilastokeskus). This dataset provides comprehensive longitudinal coverage of Finland’s national demographics over a 34-year span, featuring annual data from 1990 to 2025. The geographic scope is standardized according to the January 1, 2025 regional division, ensuring consistency across the time series despite historical administrative changes. It offers high-resolution granularity through 43 unique statistical metrics that encompass population growth, age distribution, linguistic diversity, religious affiliation and urban-rural classification. Data is reported in multiple units for versatile analysis, including absolute counts, percentages (%), and population density (persons/km²), allowing for both scale-based and proportional statistical modeling.

**type of place:** Country
**years:** 1990 to 2025

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

The refresh is automated using the provided `run.sh` script, which handles both data download and processing.

## Processing Instructions

To execute the complete import process (download and processing), run:
```bash
./run.sh
```

### Script Details:
- **Download**: The download is handled by `data_download.py` script which downloads census data from Finland's official database, formats it, and saves it to the designated file path (input_files).
- **Processing**: Uses `stat_var_processor.py` to map raw data to Data Commons StatVarObservations using the PV map and metadata configuration.

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
- `run.sh`: Main execution script for download and processing.
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