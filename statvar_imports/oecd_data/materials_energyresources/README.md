# OECD Materials And Energy Resources (city and country) - OECD Data

- source: https://www.oecd-ilibrary.org/environment/data/material-resources/mineral-and-energy-resources_21082980-en?parent=http%3A%2F%2Finstance.metastore.ingenta.com%2Fcontent%2Fcollection%2Fenv-data-en

- how to download data: Manual download from source by selecting 'Data', then choose 'Table' and click the button - 'Download'

- type of place: Country, City.

- statvars: Environment

- years: 2000 to 2022
- place_resolution: Country and City places are resolved based on name.

### How to run:

Prerequisite: The below command must be run from a folder that contains stat_var_processor.py script file.

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/oecd_data/materials_energyresources/testdata/sample_input/OECD_MaterialsAndEnergyResources_data.csv'  --pv_map='/data/statvar_imports/oecd_data/materials_energyresources/testdata/sample_input/OECD_MaterialsAndEnergyResources_pvmap.csv'  --config='/data/statvar_imports/oecd_data/materials_energyresources/testdata/sample_input/OECD_MaterialsAndEnergyResources_metadata.csv'  --output_path='/data/statvar_imports/oecd_data/materials_energyresources/testdata/sample_output/OECD_MaterialsAndEnergyResources'




