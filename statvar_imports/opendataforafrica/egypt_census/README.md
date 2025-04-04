# egypt_census_Census - Open Data For Africa

- source: https:/egypt_census.opendataforafrica.org, 

- how to download data: Manual download from source based on filter 

- type of place: City and District Level.

- statvars: Economy, Health, Education, Demographics

- years: 1988 to 2018

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/opendataforafrica/egypt_census/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/opendataforafrica/egypt_census/egypt_census_Place_Resolved.csv --config=statvar_imports/opendataforafrica/egypt_census/<filename>_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data='/statvar_imports/opendataforafrica/egypt_census/test_data/sample_input/zkjifzd.csv' --pv_map='/statvar_imports/opendataforafrica/egypt_census/pv_map/zkjifzd_pvmap.csv' --places_resolved_csv='/statvar_imports/opendataforafrica/egypt_census/egypt_census_Place_Resolved.csv' --config='/statvar_imports/opendataforafrica/egypt_census/metadata/zkjifzd_metadata.csv.csv' --output_path=/statvar_imports/opendataforafrica/egypt_census/test_data/sample_output/zkjifzd `
