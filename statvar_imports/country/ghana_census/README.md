# Country : Ghana_census

- source: https://ghana.opendataforafrica.org/

- how to download data: Manual download from source 

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Household, Health, Economy, Environment

- years: 1988 to 2010

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/country/ghana_census/pvmap/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/country/ghana_census/Ghana_place_resolver.csv --config=statvar_imports/country/ghana_census/metadata/<filename>_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/country/ghana_census/test_data/sample_input/Ghana_health.csv --pv_map=/statvar_imports/country/ghana_census/pvmap/Ghana_health_pvmap.csv --places_resolved_csv=/statvar_imports/country/ghana_census/Ghana_place_resolver.csv --config=/statvar_imports/country/ghana_census/metadata/Ghana_health_metadata.csv --output_path=/statvar_imports/country/ghana_census/test_data/sample_output/Ghana_health/`

