# NCES_HBCU_Enrollment_Import

- source:  https://nces.ed.gov/programs/digest/d23/tables/dt23_313.30.asp

- how to download data: Download script (download_script.py).
    To download the data, you'll need to run the provided download script, download_script.py. This script will automatically create an "input_files" folder where you should place the file to be processed. This script will pick up future urls also.

- type of place: Demographics.

- statvars: Demographics

- years: 1990 to 2022.

### Note:
we are retaining the data from the years 1990, 2000, and 2010 as our historical baseline. This is because with each new data release, the values for these specific years remain consistent, while the dataset is updated by incorporating one additional year of the most recent data.

### How to run:

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data='/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/input_files/<input_file.csv>' --pv_map='/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/<filename of pv_map.csv> --config_file='/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/<filename of metadata.csv>' --output_path='/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/<output_folder_name>/<filename>`

#### Download the data: 

For download the source data, run:
`python3 download_script.py`

Notes: Files will be downloaded inside "input_files" folder.

#### Process the data:

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=/data/statvar_imports/fao_currency_and_exchange_rate/fao_currency_statvar/input_files/* --pv_map=/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/nces_hbcu_pvmap.csv --config_file=/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/nces_hbcu_metadata.csv --output_path='/data/statvar_imports/us_hbcu_data/nces_hbcu_enrollment_import/output_files/nces_hbcu_output_tabn313.30'`

