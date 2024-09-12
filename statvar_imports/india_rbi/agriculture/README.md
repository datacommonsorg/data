# India RBI - Agriculture

- source: https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20States, 

- how to download data: Manual download from source based on filter - `AGRICULTURE AND ALLIED - Table 55 - 96`.

- type of place: Country and AdministrativeArea1.

- statvars: Agriculture

- years: 2005-03 to 2022-03

- place_resolution: Places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.xlsx --pv_map=statvar_imports/india_rbi/agriculture/Agriculture_pvmap.csv --places_resolved_csv=statvar_imports/statvar_imports/india_rbi/agriculture/India_places_resolved.csv --config=statvar_imports/india_rbi/agriculture/Agriculture_config_metadata.csv --output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data='statvar_imports/india_rbi/agriculture/test_data/sample_input/STATE-WISE AREA OF NON-FOODGRAINS - RAW JUTE & MESTA_data.xlsx'  --pv_map='statvar_imports/india_rbi/agriculture/Agriculture_pvmap.csv'  --config='statvar_imports/india_rbi/agriculture/Agriculture_config_metadata.csv'  --output_path=statvar_imports/india_rbi/agriculture/test_data/sample_output/State_Wise_Area_NonFood_RawJute_Mesta --places_resolved_csv='statvar_imports/india_rbi/agriculture/India_places_resolved.csv'`
