# Ethiopia Statistics

- source: https://ethiopia.opendataforafrica.org/

- how to download data: Manual download from source based on filter - 

- type of place: Country and AdministrativeArea1.

- statvars: "Demographics", "Health", "Education", "Economy"

- years: 2000 to 2022

- place_resolution:Places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data= --pv_map= --config= --output_path=

Example:
python3 stat_var_processor.py --input_data='/usr/local/google/home/kuru/ethiopiaPR/data/statvar_imports/opendataAfrica/ethiopia_statistics/test_data/ethiopia-Population_Projection_by_Region_and_Sex_2022_data.csv'  --pv_map='/usr/local/google/home/kuru/ethiopiaPR/data/statvar_imports/opendataAfrica/ethiopia_statistics/ethiopia-Population_Projection_by_Region_and_Sex_2022_pvmap.csv'  --config='/usr/local/google/home/kuru/ethiopiaPR/data/statvar_imports/opendataAfrica/ethiopia_statistics/ethiopia-Population_Projection_by_Region_and_Sex_2022_metadata.csv'  --output_path="/usr/local/google/home/kuru/ethiopiaPR/data/statvar_imports/opendataAfrica/ethiopia_statistics/test_data"
