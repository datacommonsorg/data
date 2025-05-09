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
* The pvmap for series id's are generated as per the defenitions given in https://www.bls.gov/sae/additional-resources/list-of-published-state-and-metropolitan-area-series/home.htm
* The primary series id are in the form of eg:SMS01000000000000001, here SMS refers to the adjustment method(SMS - seasonallu adjusted and SMU - seasonally unadjusted). The next two intergers (here 01) represents the state code( if the 'Area' in source is 'Statewide').
The remaining integers represent the industry (000000000000001), we saw that industries are repeating among states and we mapped the industries manually in pvmap

* Accordingly we split the actual series id into 3 different columns, one is series_type then state_id and series_id_value. So we directly took the state_id as the observationAbout. Based on this three columns we did the pvmap and place mapping in the bls_ces_state_pvmap.csv itself.




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
