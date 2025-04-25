# World Bank Commodity Market Import

- source: https://www.worldbank.org/en/research/commodity-markets, 

- how to download data: Download script (download_script.py).
    This script will create two main folders (input and output).The file to be processed will be inside input. The raw files will be inside input folder under a sub folder called downloaded_files. The processed output will be stored in output folder.

- type of place: Country (USA).

- statvars: Economy

- years: 1960 to latest (Note: Every Month data is also there for each year and also for latest year and month)


### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pv_map>.csv --config=<metadata>.csv --output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 download.py`

#### Processing

If processing from current import folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pv_map>.csv --config=<metadata>.csv --output_path=<filepath/filename>`



If processing from statvar_importer folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=test_data/monthly_price_data_input.csv --pv_map=commodity_monthly_price_pvmap.csv --config_file=commodity_monthly_price_metadata.csv -output_path=test/commodity_monthly_price_sample_output`





