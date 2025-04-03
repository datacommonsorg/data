# ZAF - Budget Data

- source: 

- how to download data: Manual download from source.

- type of place: Metropolitan Municipality.

- statvars: Economy

- years: 2018 to 2023

- place_resolution: Resolved Metropolitan Municipality name to wikidata Id manually.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/SouthAfrica/Budget/pv_map/<filename>_pvmap.csv --config=statvar_imports/SouthAfrica/Budget/ZAF_Budget_metadata.csv --output_path=--output_path=<filepath/filename>`
