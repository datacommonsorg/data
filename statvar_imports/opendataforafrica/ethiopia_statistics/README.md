# Ethiopia Statistics

- source: https://ethiopia.opendataforafrica.org/

- how to download data: Manual download from source based on filter - 

- type of place: Country and AdministrativeArea1.

- statvars: "Demographics", "Health", "Education", "Economy"

- years: 2000 to 2022

- place_resolution:Places are resolved based on name.

### How to run:

python3 stat_var_processor.py --input_data= --pv_map= --config= --places_resolved_csv= --output_path= 

Example:
python3 stat_var_processor.py --input_data='data/statvar_imports/opendataforafrica/ethiopia_statistics/test_data/ethiopia-Ethiopia_Demographics_data.csv'  --pv_map='data/statvar_imports/opendataforafrica/ethiopia_statistics/ethiopia-Ethiopia_Demographics_pvmap.csv'  --config='data/statvar_imports/opendataforafrica/ethiopia_statistics/ethiopia-Ethiopia_Demographics_metadata.csv'  --places_resolved_csv='data/statvar_imports/opendataforafrica/ethiopia_statistics/ethiopia-Ethiopia_Demographics_places_resolved.csv'  --output_path="data/statvar_imports/opendataforafrica/ethiopia_statistics/test_data/ethiopia_demographics"

