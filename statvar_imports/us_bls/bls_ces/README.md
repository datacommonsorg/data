# BLS_CES Import

- source: https://www.bls.gov/ces/ 

- how to download data: Go to https://www.bls.gov/webapps/legacy/cesbtab1.htm and select all the industries check boxes and click on "Retrieve Data".
In the new page click on "More Formatting Options" and in the "Select view of the data" field select "Multi series view" and click on "Retrieve Data", now there will be an option to download the file in xlsx

- type of place: Country.

- statvars: Economy

- years: 2015 5o 2025


### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/us_bls/bls_ces/bls_ces_pvmap.csv --config=statvar_imports/us_bls/bls_ces/bls_ces_metadata.csv --output_path=<filepath/filename>`

#### Example
#### Processing
`python3 stat_var_processor.py --input_data=statvar_imports/us_bls/bls_ces/test_data/bls_ces_input.csv --pv_map=statvar_imports/us_bls/bls_ces/bls_ces_pvmap.csv --config=statvar_imports/us_bls/bls_ces/bls_ces_metadata.csv --output_path=statvar_imports/us_bls/bls_ces/test_data/bls_ces_output`
