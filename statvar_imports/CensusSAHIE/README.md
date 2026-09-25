# CensusSAHIE

- source: https://www.census.gov/data/datasets/time-series/demo/sahie/estimates-acs.html 

- how to download data: Manually download from source based on filter - `CensusSAHIE`.

- type of place: Country

- statvars: Demographics

- years: 2008 to 2022

- place_resolution: By PVmap.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/CensusSHIE/pvmap.csv --config=statvar_imports/CensusSHIE//metadata.csv --output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/CensusSHIE/test_data/sample_input/sahie.csv --pv_map=statvar_imports/CensusSHIE/pvmap.csv  --config=statvar_imports/CensusSHIE/metadata.csv --output_path=statvar_imports/CensusSHIE/test_data/sample_output/sahie`
