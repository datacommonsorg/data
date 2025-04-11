# South Africa Census

- source: https://southafrica.opendataforafrica.org/, 

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Health, Education, Economy

- years: 1990 to 2018

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/opendataforafrica/southafrica_census/pvmap/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/opendataforafrica/southafrica_census/<filename>_places_resolved_csv.csv --config=statvar_imports/opendataforafrica/southafrica_census/metadata/<filenamm>_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example



