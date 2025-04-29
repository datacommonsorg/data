# cotedivoire_census_Census - Open Data For Africa

- source: https:/cotedivoire_census.opendataforafrica.org, 

- how to download data: Manual download from source based on filter 

- type of place: country and district level.

- statvars: Economy, Health, Education, Demographics

- years: 1988 to 2024

- place_resolution: places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/opendataforafrica/cotedivoire_census/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/opendataforafrica/cotedivoire_census/cotedivoire_census_place_resolved.csv --config=statvar_imports/opendataforafrica/cotedivoire_census/<filename>_metadata.csv --output_path=--output_path=<filepath/filename>`

### `If the Statistical Variable (SV) requires remapping, include the flag --statvar_dcid_remap_csv in above command.
--statvar_dcid_remap_csv=statvar_imports/opendataforafrica/cotedivoire_census/<filename>_remap.csv.`

#### Example
`python3 stat_var_processor.py --input_data='/statvar_imports/opendataforafrica/cotedivoire_census/test_data/sample_input/akfhutb_data.csv' --pv_map='/statvar_imports/opendataforafrica/cotedivoire_census/pv_map/akfhutb_pvmap.csv' --config='/statvar_imports/opendataforafrica/cotedivoire_census/metadata/akfhutb_metadata.csv' --output_path=/statvar_imports/opendataforafrica/cotedivoire_census/test_data/sample_output/akfhutb`
