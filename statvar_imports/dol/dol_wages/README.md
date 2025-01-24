# USA - NHTSA FARS Crash Data

- source: https://www.dol.gov/agencies/whd/state/minimum-wage/history, 

- how to download data: Download script (download_script/main.py).

- type of place: Country and State.

- statvars: Economy

- years: 1968 to 2024

- place_resolution: Places resolved to geoId in pvmap itself.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/USA/DOL_Wages/pv_map/<filename>_pvmap.csv --config=statvar_imports/USA/DOL_Wages/US_Dol_Wages_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 main.py`

#### Processing
`python3 stat_var_processor.py --input_data=statvar_imports/USA/DOL_Wages/download_script/input_files/final_data.csv --pv_map=statvar_imports/USA/DOL_Wages/pv_map/US_Dol_Wages_pvmap.csv --config=statvar_imports/USA/DOL_Wages/US_Dol_Wages_metadata.csv --output_path=--output_path=statvar_imports/USA/DOL_Wages/test_data/sample_output/US_DOL_Wages`