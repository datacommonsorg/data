# BLS CPI Category Data Importer

This document outlines the process for downloading and importing Consumer Price Index (CPI) data from the Bureau of Labor Statistics (BLS).

- **Source**: [BLS Supplemental Files](https://www.bls.gov/cpi/tables/supplemental-files/)
- **Place Type**: Country
- **Statvars**: Economy
- **Years**: 2011 to latest available data

## Usage

The process involves two main steps: downloading the source data and then processing it to generate the final output.

### 1. Download Data

A Python script is provided to download the necessary data files from the BLS website. The script organizes the files into the `input_data` directory.

**Command:**
```bash
python3 cpi_category_download.py
```
### 2. Process Data

After downloading the data, use the `stat_var_processor.py` script to process the files and generate the final statistical variables.

**Generic Command:**
```bash
../../../tools/statvar_importer/stat_var_processor.py \
    --input_data='input_data/<folder_name>/*' \
    --pv_map='<pvmap_file>.csv' \
    --config_file='<metadata_file>.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path='output/<folder_name>/<output_filename>'
```
#### Example

This example shows how to process the `cpi-w` data. To process data for `cpi-u` and `c-cpi-u`, simply update the input folder, pvmap file, config file, and output path accordingly.

**Command for `cpi-w`:**
```bash
../../../tools/statvar_importer/stat_var_processor.py \
    --input_data='input_data/cpi-w/*' \
    --pv_map='cpi_w_pvmap.csv' \
    --config_file='cpi_w_metadata.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path='output/cpi_w/cpi_w'
```
## TODO

- **Unit Testing**: Create a comprehensive unit test for the `cpi_category_download.py` script to ensure its reliability and correctness. The current download logic is complex and would benefit from a robust test suite. This will be addressed in a future update, we are keeping the bug : b/422887606 open for further tracking.
