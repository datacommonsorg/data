# Commerce_NTIA

- source:  `https://www.ntia.gov/sites/default/files/data_central_downloads/datasets/ntia-analyze-table.csv`

- NTIA programs and policymaking focus largely on expanding broadband Internet access and adoption in America, expanding the use of spectrum by all users.

- how to download data: 
    To download and process the data, you'll need to run the provided preprocess script, `preprocess.py`. This script will automatically create an "input_files" folder where you should place the file to be processed.
    By using this script, we are creating two more columns in the input files such as 'universeAgeResol', 'variableAgeResol'. This columns are created based on the universe and variable columns in the existing data.

- type of place: Demographics.

- statvars: Demographics

### How to run:

```
python3 stat_var_processor.py 
--input_data='../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/input_files/<input_file.csv>' 
--pv_map='../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/<filename of pv_map.csv>' --config_file='../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/<filename of metadata.csv>' --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path='../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/<output_folder_name>/<filename>'
```

#### Download the data: 

For download and preprocess the source data, run:
`python3 preprocess.py`

Notes: 
Files will be downloaded inside "input_files" folder (input_files/ntia-analyze-table.csv).
This preprocess script will split the downloaded input file into two files based on the age. (input_files/ntia-data.csv, input_files/ntia-data-age-only.csv) 

#### Process the data:

Execute the script inside the folder `/data/tools/statvar_importer/`

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/input_files/ntia-data.csv 
--pv_map=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_pvmap.csv 
--config_file=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/output_files/ntia_output
```

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/input_files/ntia-data-age-only.csv 
--pv_map=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_age_pvmap.csv 
--config_file=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/ntia_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/ntia_internet_use_survey/Commerce_NTIA/output_files/ntia_age_output
```

