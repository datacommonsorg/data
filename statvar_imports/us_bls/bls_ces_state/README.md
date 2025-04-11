# BLS_CES Import

- source: https://www.bls.gov/ces/ 

### Download
- How to download data: We have the download script bls_ces_state_download_script.py to download the data from source website and keep csv files inside the raw_data folder.
### How to run:
`python3 bls_ces_state_download_script.py --state=<specific state naem to download it's data>
### Example:
`python3 bls_ces_state_download_script.py'

- type of place: State.

- statvars: Economy

- years: 1939 5o 2025

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/us_bls/bls_ces_state/bls_ces_state_pvmap.csv --config=statvar_imports/us_bls/bls_ces_state/bls_ces_state_metadata.csv --output_path=<filepath/filename>`

#### Example
#### Processing
`python3 stat_var_processor.py --input_data=statvar_imports/us_bls/bls_ces_state/test_data/bls_ces_input.csv --pv_map=statvar_imports/us_bls/bls_ces_state/bls_ces_pvmap.csv --config=statvar_imports/us_bls/bls_ces_state/bls_ces_metadata.csv --output_path=statvar_imports/us_bls/bls_ces_state/test_data/bls_ces_output`
