# FAO_Currency_statvar

- source:  https://bulks-faostat.fao.org/production/Exchange_rate_E_All_Data.zip

- how to download data: Download script (download.sh).
    To download the data, you'll need to run the provided download script, download.sh. This script will automatically create an "input_data" folder where you should place the file to be processed. After the download, we have to run the script (preprocess.py) before the actual processing begins.

- type of place: Demographics.

- statvars: Demographics

- years: 1970 to 2024.

- place_resolution: Places resolved in place_resolver sheet separately.

### How to run:

`python3 stat_var_processor.py --input_data='/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/input_data/<input_file.csv>' --pv_map='/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/<filename of pv_map.csv> --places_resolved_csv='/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/<filename of place_map.csv>' --config_file='/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/<filename of metadata.csv>' --output_path='/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/<output_folder_name>/<filename>`

#### Download the data: 

For download the source data, run:
`sh download.sh`

For preprocess the input data, run:
`python3 preprocess.py`

Notes: Files will be downloaded inside "input_data" folder (final_input_data.csv).

#### Processing the data:

`python3 stat_var_processor.py --input_data=/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/input_data/final_input_data.csv --pv_map=/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/CurrencyFAO_pv_map.csv --config=/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/CurrencyFAO_metadata.csv --places_resolved_csv=/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/CurrencyFAO_place_map.csv --output_path='/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/output_files/CurrencyFAO_output'`

