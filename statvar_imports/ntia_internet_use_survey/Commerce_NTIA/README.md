# Commerce_NTIA

- source:  `https://www.ntia.gov/sites/default/files/data_central_downloads/datasets/ntia-analyze-table.csv`

- NTIA programs and policymaking focus largely on expanding broadband Internet access and adoption in America, expanding the use of spectrum by all users.

- how to download data: 
    Download script (ntia_download.py).
    To download the data, you'll need to run the provided download script, 'ntia_download.py'. This script will automatically create an "input_files" folder where you should place the file to be processed. After that run 'preprocess.py' for preprocessing the data. In this script, we are creating two more columns in the input files such as 'universeAgeResol', 'variableAgeResol'. This columns are created based on the universe and variable columns in the existing data.

- type of place: Demographics.

- statvars: Demographics

- years: 1994 to 2023.

### How to run:

`python3 stat_var_processor.py --input_data='/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/input_files/<input_file.csv>' --pv_map='/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/<filename of pv_map.csv> --config_file='/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/<filename of metadata.csv>' --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/<output_folder_name>/<filename>`

#### Download the data: 

For download the source data, run:
`python3 ntia_download.py`

Notes: Files will be downloaded inside "input_files" folder (input_files/ntia-analyze-table.csv).

To preprocess the downloaded data:, run:
`python3 preprocess.py`

Note: This preprocess script will split the downloaded input file into two files based on the age. (input_files/ntia-data.csv, input_files/ntia-data-age-only.csv) 

#### Process the data:

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/input_files/ntia-data.csv --pv_map=/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_pvmap.csv --config_file=/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/output_files/ntia_output'`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/input_files/ntia-data-age-only.csv --pv_map=/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_age_pvmap.csv --config_file=/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='/data/statvar_imports/ntia_internet_use_survey/Commerce_NTIA/output_files/ntia_age_output'`

