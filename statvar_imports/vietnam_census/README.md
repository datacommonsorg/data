# Vietnam Census

- source: https://www.gso.gov.vn/en/homepage/, 

- how to download data: Download script (viet_download.py.py).
    This script will create one main folders(input) having 12 .xlxs files to be processed. 

- type of place: Country (Vietnam).


- years: 1995 to latest.


### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pv_map>.csv --config=<metadata>.csv --output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 download.py`

#### Processing

If processing from current import folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pv_map>.csv --config=<metadata>.csv --output_path=<filepath/filename>`



If processing from statvar_importer folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=<input_files>.csv --pv_map=<pvmap>.csv --config_file=<metadata>.csv -output_path=<filepath/filename>`





