# USMonthlyRetailSales - Monthly Retail Sales US Census

- source: https://www.census.gov/retail/

- how to download data: To download the data, execute download.py. This will place the input files inside the input_files folder.

- statvars: Economy

- years: 1992 to 2025

### How to run:

`python3 stat_var_processor.py --input_data='/statvar_imports/us_monthly_retail_sales/test_data/<filename>.xlsx' --pv_map="/statvar_imports/us_monthly_retail_sales/<filename>.csv" --statvar_dcid_remap_csv="/statvar_imports/us_monthly_retail_sales/<filename>.csv" --output_path='/statvar_imports/us_monthly_retail_sales/test_data/<filename>' --config="/statvar_imports/us_monthly_retail_sales/<filename>.csv`

### `If the Statistical Variable (SV) requires remapping, include the flag --statvar_dcid_remap_csv in above command.
--statvar_dcid_remap_csv=/statvar_imports/us_monthly_retail_sales/monthly_retail_remap.csv`

#### Example
`python3 stat_var_processor.py --input_data='/statvar_imports/us_monthly_retail_sales/test_data/sample_input.xlsx' --pv_map="/statvar_imports/us_monthly_retail_sales/monthly_retail_pvmap.csv" --statvar_dcid_remap_csv="/statvar_imports/us_monthly_retail_sales/monthly_retail_remap.csv" --output_path='/statvar_imports/us_monthly_retail_sales/test_data/sample_output' --config="/statvar_imports/us_monthly_retail_sales/monthly_retail_metadata.csv`
