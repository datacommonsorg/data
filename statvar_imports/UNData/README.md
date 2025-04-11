# UNData Import

- source: https://data.un.org/Data.aspx?q=city+population&d=POP&f=tableCode%3a240, 


- type of place: City.

- statvars: Demography

- years: 1968 to 2024

- place_resolution: Places resolved to wikidataId.

### How to run:

`python3 download.py`
This will create input_file folder along with input file.


`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/UNData/UNData_pvmap.csv --config_file=statvar_imports/UNData/UNData_metadata.csv --output_path=--output_path=output/UNData.csv --places_resolved_csv='statvar_imports/UNData/places_resolved_csv.csv'`

The output generated from above script needs to be more filtered so as to remove sudden data spikes and drops which seems wrong. Run below command on the output csv and use the output generated from below code as final output:

`python3 filter_data_outliers.py --filter_data_input=output/UNData.csv --filter_data_output=UNData-filtered.csv --filter_data_min_value=2 --filter_data_max_change_ratio=1 --filter_data_max_yearly_change_ratio=0.5`

#### Example

#### Processing
`python3 download.py`

`python3 stat_var_processor.py --input_data=<input_files>.csv --pv_map=statvar_imports/UNData/UNData_pvmap.csv --config=statvar_imports/UNData/UNData_metadata.csv --output_path=statvar_imports/UNData/output/UNData.csv -places_resolved_csv='statvar_imports/UNData/places_resolved_csv.csv'`

`python3 filter_data_outliers.py --filter_data_input=output/UNData.csv --filter_data_output=statvar_imports/UNData/output/UNData-filtered.csv --filter_data_min_value=2 --filter_data_max_change_ratio=1 --filter_data_max_yearly_change_ratio=0.5`
