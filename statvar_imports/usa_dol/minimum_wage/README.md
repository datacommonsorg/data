# USA_DOL_Wages Import

- source: https://www.dol.gov/agencies/whd/state/minimum-wage/history, 

- how to download data: Download script (download_script/main.py).
    This script will create two folders (input_files and source_files).The file to be processed will be inside input_files. The raw files will be inside source_files folder

- type of place: Country and State.

- statvars: Economy

- years: 1968 to 2024

- place_resolution: Places resolved to geoId in pvmap itself.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/usa_dol/minimum_wage/<filename>_pvmap.csv --config=statvar_imports/usa_dol/minimum_wage/US_Dol_Wages_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 main.py`

#### Processing
`python3 stat_var_processor.py --input_data=statvar_imports/usa_dol/minimum_wage/download_script/input_files/final_data.csv --pv_map=statvar_imports/usa_dol/minimum_wage/us_dol_wages_pvmap.csv --config=statvar_imports/usa_dol/minimum_wage/us_dol_wages_metadata.csv --output_path=statvar_imports/usa_dol/minimum_wage/test_data/sample_output/us_dol_wges`
