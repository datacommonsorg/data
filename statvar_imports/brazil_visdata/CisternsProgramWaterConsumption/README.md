# Brazil - Cisterns Program Water Consumption

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Brazil Food Acquisition Program Action to Specific Population Groups`.

- type of place: Country and Municipality level.

- statvars: Demographics, Household

- years: 2008 to 2023

- place_resolution: Places resolved based on municipalty code.
- License: 

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/test_data/sample_input/<input_file>.csv --pv_map=/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/pv_map/<filename>_pvmap.csv --config=/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/pv_map/<metadata-file-name>.csv --output_path=/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/test_data/sample_output/<Filename>

### for example:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/test_data/sample_input/Family_water_cisterns_for_consumption_(1st water)_delivered_by_MDS_(Accumulated) - data.csv'   --pv_map='/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/pv_map/Family_water_cisterns_for_consumption_(1st water)_delivered_by_MDS_(Accumulated) - pvmap.csv'    --config='/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/pv_map/Family_water_cisterns_for_consumption_(1st water)_delivered_by_MDS_(Accumulated) - metadata.csv'   --output_path='/data/statvar_imports/brazil_visdata/CisternsProgramWaterConsumption/test_data/sample_output/Family_water_cisterns_for_consumption_(1st water)_delivered_by_MDS_(Accumulated)'
