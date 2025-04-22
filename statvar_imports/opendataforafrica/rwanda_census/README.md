# Rwanda Census

- source: https://rwanda.opendataforafrica.org/

- how to download data: Manual download from source based on filter - 

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Economy, Education

- years: 2002 to 2023

- place_resolution:Places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=/data/statvar_imports/opendataforafrica/rwanda_census/test_data/ztaoyl_data.csv --pv_map=/data/statvar_imports/opendataforafrica/rwanda_census/ztaoyl_pv_map.csv --config=/data/statvar_imports/opendataforafrica/rwanda_census/ztaoyl_metadata.csv --output_path=/data/statvar_imports/opendataforafrica/rwanda_census/test_data/ztaoyl`

## If place resolution is involved,use:
` --places_resolved_csv=data/statvar_imports/opendataforafrica/rwanda_census/places_resolved_csv.csv` along with the remaining command.

## If statvar remap is involved,use:
` --statvar_dcid_remap_csv=data/statvar_imports/opendataforafrica/rwanda_census/edvtatd_statvar_remap.csv` along with the remaining command for that particular file.