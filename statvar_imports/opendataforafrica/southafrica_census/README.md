# South Africa Census

- source: https://southafrica.opendataforafrica.org/, 

- type of place: Country and AdministrativeArea1.

- how to download data: Manual download from source based on filter

- statvars: Demographics, Health, Education, Economy

- years: 1990 to 2018

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=data/statvar_imports/opendataforafrica/southafrica_census/pvmap/<filename>_pvmap.csv --places_resolved_csv=data/statvar_imports/opendataforafrica/southafrica_census/<filename>_places_resolved_csv.csv --config=data/statvar_imports/opendataforafrica/southafrica_census/metadata/<filenamm>_metadata.csv --output_path=--output_path=<filepath/filename>`

## If place resolution is involved,use:

` --places_resolved_csv=data/statvar_imports/opendataforafrica/southafrica_census/places_resolved_csv.csv` along with the remaining command.
