# ITA Economic Activity - US Data

- source: 

- how to download data: Manual download from source by selecting the values from the dropdowns - 'Product' and 'Trade Flow' and then click on the button - 'Download Symbol'

- type of place: Country, Geographical Region.

- statvars: Economy

- years: 2009 to 2022
- place_resolution: Country and Geographical Region places are resolved based on name.

### How to run:

Prerequisite: The below command must be run from a folder that contains stat_var_processor.py script file.

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/testdata/sample_input/US_ITA_data.csv' --pv_map='data/statvar_imports/testdata/sample_input/US_ITA_pvmap.csv' --places_resolved_csv='data/statvar_imports/testdata/sample_input/US_ITA_places_resolved.csv' --config='data/statvar_imports/testdata/sample_input/US_ITA_metadata.csv' --output_path="data/statvar_imports/testdata/sample_output/US_ITA"


 

