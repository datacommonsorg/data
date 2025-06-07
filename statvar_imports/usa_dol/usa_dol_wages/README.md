# USA_DOL_Wages Import

- source: https://www.dol.gov/agencies/whd/state/minimum-wage/history, 

- how to download data: Download script (usa_dol_wages_download_script.py).
    This script will create two folders (input_files and source_files).The file to be processed will be inside input_files. The raw files will be inside source_files folder

- type of place: Country and State.

- statvars: Economy

- years: 1968 to 2024

- place_resolution: Places resolved to geoId in pvmap itself.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/usa_dol/usa_dol_wages/usa_dol_wages_pvmap.csv --config=statvar_imports/usa_dol/usa_dol_wages/usa_dol_wages_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 usa_dol_wages_download_script.py`

#### Processing
If processing from current import folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/final_data.csv --pv_map=us_dol_wages_pvmap.csv --config_file=us_dol_wages_metadata.csv --output_path=output/us_dol`

If processing from statvar_importer folder :

`python3 stat_var_processor.py --input_data=data/statvar_imports/usa_dol/usa_dol_wages/input_files/final_data.csv --pv_map=data/statvar_imports/usa_dol/usa_dol_wages/us_dol_wages_pvmap.csv --config=data/statvar_imports/usa_dol/usa_dol_wages/us_dol_wages_metadata.csv --output_path=data/statvar_imports/usa_dol/usa_dol_wages/output/us_dol_wges`
