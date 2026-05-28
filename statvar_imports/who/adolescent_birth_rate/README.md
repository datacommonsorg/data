# WHO Adolescent Birth Rate Import

## Overview
This dataset contains national and regional-level statistics for the Adolescent Birth Rate (per 1,000 women).
Specifically, it provides data for two distinct age groups:
- 10-14 years (Y10T14)
- 15-19 years (Y15T19)

**type of place:** Country, Region (M49 codes), WHO Regions, Overseas Territory, Special Administrative Regions
**years:** 2000 to 2024
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:europe, dcid:LatinAmericaAndCaribbean)

## Data Source
**Source URL:**
https://data.who.int/indicators/i/24C65FE/27D371A

**Provenance Description:**
The data comes from the World Health Organization (WHO). It specifically tracks Sustainable Development Goal (SDG) Indicator 3.7.2, measuring the adolescent birth rate (per 1,000 women aged 10–14 and 15–19) globally across different geographic classifications.

## Refresh Type
Automatic Refresh

For refresh of the data, the import includes a Python script (`data_download.py`) to automatically download the complete historical dataset directly from the WHO's backend Azure Blob storage endpoint.

## Data Publish Frequency
Release Frequency = Annual

## How To Download Input Data
To download the data, run the provided script:
```bash
python3 data_download.py
```

This will fetch the latest full dataset and save it locally as `input_files/adolescent_birth_rate_data.csv`, making it available for processing.

## Processing Instructions
To process the WHO Adolescent Birth Rate data and generate statistical variables, use the following command from the `adolescent_birth_rate` directory:

**For Data Run**
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data=input_files/* \
    --pv_map=adolescent_birth_rate_pvmap.csv \
    --output_path=adolescent_birth_rate_output \
    --config_file=adolescent_birth_rate_metadata.csv
```

This generates the following output files:
- adolescent_birth_rate_output.csv
- adolescent_birth_rate_output_stat_vars_schema.mcf
- adolescent_birth_rate_output_stat_vars.mcf
- adolescent_birth_rate_output.tmcf

**For Data Quality Checks and validation**
Validation of the data is done using the lint flag in the DataCommons import tool
```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar lint adolescent_birth_rate_output_stat_vars_schema.mcf adolescent_birth_rate_output.csv adolescent_birth_rate_output.tmcf adolescent_birth_rate_output_stat_vars.mcf
```

This generates the following output files:
- report.json
- summary_report.csv
- summary_report.html

The report files can be analyzed to check for errors and warnings. Further, linting is performed on the generated output files using the DataCommons import tool.

## Testing
Testing is performed using the provided `test_data` directory:
- Input: `test_data/adolescent_birth_rate_input.csv`
- Output (expected): `test_data/adolescent_birth_rate_output.csv`
- MCF (expected): `test_data/adolescent_birth_rate_output.tmcf`
