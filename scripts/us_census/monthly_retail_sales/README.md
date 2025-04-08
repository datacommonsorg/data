# USMonthlyRetailSales - Monhtly Retail Sales US Census

- source: https://www.census.gov/retail/

- how to download data: Manual download from source based on filter 

- statvars: Economy

- years: 1992 to 2025

### How to run:

`python3 stat_var_processor.py --input_data='/scripts/us_census/monthly_retail_sales/test_data/sample_input/<filename>.xlsx' --pv_map="/scripts/us_census/monthly_retail_sales/pv_map/<filename>.csv" --statvar_dcid_remap_csv="/scripts/us_census/monthly_retail_sales/remap/<filename>.csv" --output_path='/scripts/us_census/monthly_retail_sales/test_data/sample_output/<filename>' --config="/scripts/us_census/monthly_retail_sales/metadata/<filename>.csv`

### `If the Statistical Variable (SV) requires remapping, include the flag --statvar_dcid_remap_csv in above command.
--statvar_dcid_remap_csv=/scripts/us_census/monthly_retail_sales/remap/remap.csv`

#### Example
	`python3 stat_var_processor.py --input_data='/scripts/us_census/monthly_retail_sales/test_data/sample_input/input_data.xlsx' --pv_map="/scripts/us_census/monthly_retail_sales/pv_map/monthly_retail_pvmap.csv" --statvar_dcid_remap_csv="/scripts/us_census/monthly_retail_sales/remap/remap.csv" --output_path='/scripts/us_census/monthly_retail_sales/test_data/sample_output/sample_output' --config="/scripts/us_census/monthly_retail_sales/metadata/monthly_retail_metadata.csv`
