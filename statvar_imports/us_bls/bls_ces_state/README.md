# BLS_CES_State Import

- source: https://www.bls.gov/ces/ 

- How to download data: We have the download script bls_ces_download_script.py to download the data from source website and keep csv files inside the input_files folder.
### How to run download script:
`python3 ../download_bls_ces_data.py --place_type=state input_folder=bls_ces_state
### Example:
`python3 ../download_bls_ces_data.py --place_type=state input_folder=bls_ces_state

- type of place: State and county.

- statvars: Economy

- years: 1939 till latest available data
- As the source api is not having historical data available, we are keeping the data from 1936 - 2019 as a historical data and refreshing data from 2020 till latest available data

### How to run:
To process from current import folder

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=<input_file>.csv --pv_map=data/statvar_imports/us_bls/bls_ces_state/bls_ces_state_pvmap.csv --config_file=data/statvar_imports/us_bls/bls_ces_state/bls_ces_state_metadata.csv --output_path=<filepath/filename>`

#### Example

#### Download
Running from current import folder(bls_ces_state)
`python3 ../download_bls_ces_data.py --place_type=state input_folder=bls_ces_state

#### Processing
Running from current import folder(bls_ces_state)
`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/merged_output.csv --pv_map=bls_ces_state_pvmap.csv --config_file=bls_ces_state_metadata.csv --output_path=output/bls_ces_state`
