# US CPI Data Importer

This document outlines the process for downloading and importing Consumer Price Index (CPI) data from the Bureau of Labor Statistics (BLS).

- **Source**: [BLS Supplemental Files](https://www.bls.gov/cpi/tables/supplemental-files/)
- **Place Type**: Country and Regions
- **Statvars**: Economy
- **Years**: 2011 to latest available data

## Usage

The process involves two main steps: downloading the source data and then processing it to generate the final output.

### 1. Download Data

A Python script is provided to download the necessary data files from the BLS website. The script organizes the files into the `input_data` directory, we have to give the output folder using the --output_folder flag . The script is located at /statvar_imports/us_bls/cpi_category/cpi_category_download.py

**Command:**
From the statvar_imports/us_bls/us_cpi directory, run the following
         command:
```bash
python3 ../cpi_category/cpi_category_download.py --output_folder=../us_cpi/input_data
```
### 2. Process Data

After downloading the data, use the `stat_var_processor.py` script to process the files and generate the final statistical variables.

#### Note : 
Currently we are taking the consumerGoodsCategory directly from the input data using a #Eval in the pvmap, so if there is a new entry for goods category or any change in the existing goods category it will cause the addition of a new schema.

#### Example

This example shows how to process the `cpi-w` data. To process data for `cpi-u`, simply update the input folder to get the output respectively(pvmap and metadata are the same for both).

**Command for `cpi-u`:**
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data='input_data/cpi-u/*' \
    --pv_map='us_cpi_pvmap.csv' \
    --config_file='us_cpi_metadata.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path='output/cpi_u'
```
## TODO : b/436491943

- **Making output general**: As we are taking the consumerGoodsCategory directly from the source file(using #Eval in pvmap), any change in the source data is creating another series. To resolve this make whole output data generic
- **Merging with BLS_CPI_Category import**: The BLS_CPI_Category import is also importing the same data using different configs present in '/statvar_imports/us_bls/cpi_category/' folder, need to analyze and merge these two if entire sv's are same

