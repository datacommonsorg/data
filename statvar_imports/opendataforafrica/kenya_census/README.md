# Kenya Census

- source: https://kenya.opendataforafrica.org/

- how to download data: Manual download from source based on filter - 

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Economy, Education

- years: 2002 to 2023

- place_resolution:Places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=/data/statvar_imports/opendataforafrica/kenya_census/test_data/dlrrjxg_input.csv --pv_map=/data/statvar_imports/opendataforafrica/kenya_census/dlrrjxg_pvmap.csv --config=/data/statvar_imports/opendataforafrica/kenya_census/dlrrjxg_metadata.csv --output_path=/data/statvar_imports/opendataforafrica/kenya_census/test_data/dlrrjxg`

## If place resolution is involved,use:
` --places_resolved_csv=data/statvar_imports/opendataforafrica/kenya_census/places_resolved_csv.csv` along with the remaining command.