# USA - NHTSA FARS Crash Data

- source: https://www.dol.gov/agencies/whd/state/minimum-wage/history, 

- how to download data: Manual download from source.

- type of place: Country and State.

- statvars: Economy

- years: 1968 to 2023

- place_resolution: Resolved state name to state geoId using places resolved csv.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/USA/DOL_Wages/pv_map/<filename>_pvmap.csv --config=statvar_imports/USA/DOL_Wages/US_Dol_Wages_metadata.csv --places_resolved_csv=statvar_imports/USA/DOL_Wages/USA_State_Places_resolved.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/USA/DOL_Wages/test_data/sample_input/US_Dol_Wages_data.csv --pv_map=statvar_imports/USA/DOL_Wages/pv_map/US_Dol_Wages_pvmap.csv --config=statvar_imports/USA/DOL_Wages/USA_State_Places_resolved.csv --output_path=--output_path=statvar_imports/USA/DOL_Wages/test_data/sample_output/US_DOL_Wages`