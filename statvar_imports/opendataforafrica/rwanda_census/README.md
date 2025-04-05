# Rwanda Census

- source: https://rwanda.opendataforafrica.org/

- how to download data: Manual download from source based on filter - 

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Economy, Education

- years: 2002 to 2023

- place_resolution:Places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=/usr/local/google/home/chharish/opendata_africa/data/statvar_imports/opendataforafrica/rwanda_census/test_data/ztaoyl_data.csv --pv_map=/usr/local/google/home/chharish/opendata_africa/data/statvar_imports/opendataforafrica/rwanda_census/ztaoyl_pv_map.csv --config=/usr/local/google/home/chharish/opendata_africa/data/statvar_imports/opendataforafrica/rwanda_census/ztaoyl_metadata.csv --output_path=/usr/local/google/home/chharish/opendata_africa/data/statvar_imports/opendataforafrica/rwanda_census/test_data/ztaoyl`
