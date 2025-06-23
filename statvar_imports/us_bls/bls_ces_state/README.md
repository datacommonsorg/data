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

### pvmap:
The pvmap for series IDs was generated manually based on the definitions provided at https://www.bls.gov/sae/additional-resources/list-of-published-state-and-metropolitan-area-series/home.htm. 

This process included a manual mapping of industries due to observed repetitions across states.

The primary series IDs follow a format such as SMS01000000000000001, where:
- 'SMS' indicates the adjustment method (Seasonally Adjusted). 'SMU' represents Seasonally Unadjusted.
- The subsequent two digits (e.g., '01') represent the state code, specifically when the 'Area' in the source is 'Statewide'.
- The remaining digits represent the industry code (e.g., 000000000000001). Due to the repetition of these industry codes across different states, we performed a manual mapping of industries in the pvmap.

To facilitate this mapping, we split the original series ID into three distinct columns: 'series_type', 'state_id', and 'series_id_value'. We then directly used the 'state_id' as the observationAbout. The resulting pvmap and place mappings were consolidated within the `bls_ces_state_pvmap.csv` file.



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
