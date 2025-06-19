# USA_DOL_Wages Import

- source: https://www.dol.gov/agencies/whd/state/minimum-wage/history, 

- type of place: Country and State.

- statvars: Economy

- years: 1968 to 2024

- place_resolution: Places resolved to geoId in pvmap itself.


#### Download : 

`python3 usa_dol_wages_download_script.py`

- Run the download script: python3 usa_dol_wages_download_script.py. Upon completion, you'll find two   new directories: source_files, which holds the original downloaded content, and input_files, which contains the cleaned and finalized data. The input_files folder should be considered as your primary input

### How to run:

`python3 stat_var_processor.py --input_data=../../statvar_imports/usa_dol/minimum_wage/download_script/input_files/final_data.csv --pv_map=../../statvar_imports/usa_dol/minimum_wage/us_dol_wages_pvmap.csv --config=../../statvar_imports/usa_dol/minimum_wage/us_dol_wages_metadata.csv --output_path=../../statvar_imports/usa_dol/minimum_wage/test_data/sample_output/us_dol_wges`
