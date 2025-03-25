# SouthAfrica_Budget Import

- source: https://github.com/dsfsi/data-commons-data/tree/master/data/budget%20data/csv, 

- type of place: Country and State.

- statvars: Economy

- years: 2018 to 2023

- place_resolution: Places resolved to geoId in pvmap itself.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/southafrica/budget/<filename>_pvmap.csv --config=statvar_imports/southafrica/budget/SouthAfrica_Budget_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 main.py`

#### Processing
`python3 stat_var_processor.py --input_data=statvar_imports/southafrica/budget/download_script/input_files/final_data.csv --pv_map=statvar_imports/southafrica/budget/SouthAfrica_Budget_pvmap.csv --config=statvar_imports/southafrica/budget/SouthAfrica_Budget_metadata.csv --output_path=statvar_imports/southafrica/budget/test_data/sample_output/SouthAfrica_Budget`
