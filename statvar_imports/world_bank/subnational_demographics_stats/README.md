# Subnational_Demographics_Stats

- source:  `https://databank.worldbank.org/source/subnational-population`

- Sub-national Demographic data - Worldbank Population for Country and States.

- how to download data: 
    To download the data, you'll need to run the download script, `download_data.py`. This script will automatically create an "input_files" folder where you should place the file to be processed.

### How to run:

```
python3 ../../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/<input_file_name>.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--pv_map=wb_subnational_pvmap.csv 
--config_file=wb_subnational_metadata.csv 
--places_resolved_csv=wb_subnational_place_resolution.csv 
--output_path=output_files/<output_file_name>
```

#### Download the data: 

For download the source data, run:
`python3 download_data.py`

Notes: 
Files will be downloaded inside "input_files" folder (`input_files/P_Data_Extract_From_Subnational_Population.zip`).
After preprocessing the data, final input file will be `input_files/wb_subnational_input.csv`.

#### Process the data:

Execute the script inside the folder `/data/tools/statvar_importer/`

```
python3 ../../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/wb_subnational_input.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--pv_map=wb_subnational_pvmap.csv 
--config_file=wb_subnational_metadata.csv 
--places_resolved_csv=wb_subnational_place_resolution.csv 
--output_path=output_files/wb_subnational_output
```

