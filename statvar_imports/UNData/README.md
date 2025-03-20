# UNData Import

- source: https://data.un.org/Data.aspx?q=city+population&d=POP&f=tableCode%3a240, 


- type of place: City.

- statvars: Demography

- years: 1968 to 2024

- place_resolution: Places resolved to geoId.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/UNData/<filename>_pvmap.csv --config=statvar_imports/UNData/UNData_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example

#### Processing
`python3 stat_var_processor.py --input_data=<input_files>.csv --pv_map=statvar_imports/UNData/UNData_pvmap.csv --config=statvar_imports/UNData/UNData_metadata.csv --output_path=statvar_imports/UNData/output/`
