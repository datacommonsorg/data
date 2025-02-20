# USA - NHTSA FARS Crash Data

- source: https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/, 

- how to download data: Manual download from source.

- type of place: Country, State and County.

- statvars: Demographics

- years: 1975 to 2022

- place_resolution: FIPS code present in data sheet.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/USA/NHTSA_FARS_CrashData/pv_map/<filename>_pvmap.csv --config=statvar_imports/USA/NHTSA_FARS_CrashData/test_data/common_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/USA/NHTSA_FARS_CrashData/test_data/sample_input/accident_1975Onwards_data.csv --pv_map=statvar_imports/USA/NHTSA_FARS_CrashData/pv_map/accident_1975Onwards_pvmap.csv --config=statvar_imports/USA/NHTSA_FARS_CrashData/test_data/common_metadata.csv --output_path=--output_path=statvar_imports/USA/NHTSA_FARS_CrashData/test_data/sample_output/accident_1975Onwards`