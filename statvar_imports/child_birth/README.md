# child_birth

The data set contains USA birth data

Download:
Data download URL : https://data.cdc.gov/api/views/hmz2-vwda/rows.csv?accessType=DOWNLOAD

###Execution steps :

To Download, run:

python3 download_util_script.py --download_url=https://data.cdc.gov/api/views/hmz2-vwda/rows.csv?accessType=DOWNLOAD --output_folder=input_files/

Note : The downloaded file will be saved as "input_files/rows.csv"

###How to run:

python3 stat_var_processor.py 
--input_data=../../statvar_imports/child_birth/input_files/*.csv \
--pv_map=../../statvar_imports/child_birth/pv_map.csv \
--places_resolved_csv=../../statvar_imports/child_birth/place_mapping.csv \ 
--config_file=../../statvar_imports/child_birth/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \ 
--output_path=../../statvar_imports/child_birth/output_files/child_birth 



###Example

To Process the files, Run:

Execute the script inside the folder "/data/tools/statvar_importer/"

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/child_birth/input_files/*.csv 
--pv_map=../../statvar_imports/child_birth/pvmap.csv
--places_resolved_csv=../../statvar_imports/child_birth/places_resolved.csv 
--config_file=../../statvar_imports/child_birth/metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/child_birth/output_files/child_birth
```


