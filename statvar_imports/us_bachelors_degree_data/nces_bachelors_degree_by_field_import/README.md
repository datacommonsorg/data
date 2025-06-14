# NCES_Bachelors_Degree_By_Field_Import

- source:  https://nces.ed.gov/programs/digest/d23/tables/dt23_322.50.asp

- how to download data: Download script (download_data.py).
    To download the data, you'll need to run the provided download script, download_data.py. This script will automatically create an "input_files" folder where you should place the file to be processed.

#### Download the data: 

For download the source data, run:

`python3 download_data.py`

Notes: Files will be downloaded inside "input_files" folder

#### Processing the data:
Execute the script inside the folder "/data/statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/"

`./../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/table_50_*.xlsx --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --pv_map=table50_female_pvmap.csv --config_file=metadata.csv --output_path='output_files/nces_female_output`

`../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/table_40_*.xlsx --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --pv_map=table40_male_pvmap.csv --config_file=metadata.csv --output_path=output_files/nces_male_output`

