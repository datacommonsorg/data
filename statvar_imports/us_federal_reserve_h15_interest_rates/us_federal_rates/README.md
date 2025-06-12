# US_Federal_Rates

- source:  `https://www.federalreserve.gov/DataDownload/Choose.aspx?rel=H15`

- how to download data: 
    Download script (us_fed_download.py).
    To download the data, you'll need to run the provided download script, 'us_fed_download.py'. This script will automatically create an "input_files" folder where you should place the file to be processed. This import uses one config.py file for storing the urls.

- type of place: Demographics.

### How to run:

`python3 stat_var_processor.py --input_data='/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/input_files/<input_file.csv>' --pv_map='/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/<filename of pv_map.csv> --config_file='/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/<filename of metadata.csv>' --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/<output_folder_name>/<filename>`

#### Download the data: 

For download the source data, run:

`python3 us_fed_download.py`

Notes: Files will be downloaded inside "input_files" folder (input_files/us_fed_input_*.csv).

#### Process the data:

`python3 stat_var_processor.py --input_data=/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/input_files/us_fed_input_1.csv --pv_map=/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/us_fed_fund_pvmap.csv --config_file=/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/us_fed_fund_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/output_files/us_fed_fund_output'`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/input_files/us_fed_input_2.csv --pv_map=/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/us_fed_interest_rates_pvmap.csv --config_file=/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/us_fed_interest_rates_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='/data/statvar_imports/us_federal_reserve_h15_interest_rates/us_federal_rates/output_files/us_fed_interest_rate_output'`

