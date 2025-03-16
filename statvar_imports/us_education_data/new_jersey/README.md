# New Jersey - US Education Data

- source: https://rc.doe.state.nj.us/download 

- how to download data: Manual download from source based on filter - `School Year`.

- type of place: Country and AdministrativeArea1.

- statvars: Education

- years: 2017 to 2023

- place_resolution: State places are resolved based on name.

### How to run:

Prerequisite: The below command must be run from a folder that contains stat_var_processor.py script file.

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/us_education_data/new_jersey/testdata/sample_input/US_EDU_NJ_data.csv'  --pv_map='/data/statvar_imports/us_education_data/new_jersey/testdata/sample_input/US_EDU_NJ_pvmap.csv'  --places_resolved_csv='/data/statvar_imports/us_education_data/new_jersey/testdata/sample_input/US_EDU_NJ_places_resolved.csv'  --config='/data/statvar_imports/us_education_data/new_jersey/testdata/sample_input/US_EDU_NJ_metadata.csv'   --output_path='/data/statvar_imports/us_education_data/new_jersey/testdata/sample_output/us_edu_nj'

