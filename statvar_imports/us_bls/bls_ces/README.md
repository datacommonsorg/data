# BLS_CES Import

- source: https://www.bls.gov/ces/ 

- How to download data: We have the download script bls_ces_download_script.py to download the data from source website and keep csv files inside the input_files folder.
### How to run:
`python3 ../bls_ces_download_script.py --place_type=national input_folder=bls_ces
### Example:
`python3 bls_ces_download_script.py --place_type=national input_folder=bls_ces`

- type of place: Country.

- statvars: Economy

- years: 2015 till latest available data


### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=data/statvar_imports/us_bls/bls_ces/bls_ces_pvmap.csv --config_file=data/statvar_imports/us_bls/bls_ces/bls_ces_metadata.csv --output_path=<filepath/filename>`

#### Example

#### Download
`python3 bls_ces_download_script.py --place_type=national input_folder=bls_ces`

#### Processing
`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/merged_output.csv --pv_map=bls_ces_pvmap.csv --config_file=bls_ces_metadata.csv --output_path=output/bls_ces_state`
