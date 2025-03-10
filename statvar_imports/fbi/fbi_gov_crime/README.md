# FBIGovCrime Import

- source: https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads 

- how to download data: Download script (download_script/download_script.py).
    This script will create two folders (download_folder and download_folder/input_files).The file to be processed will be inside input_files.

- type of place: City.

- statvars: Crime

- years: 2020 to 2023

- place_resolution: Places resolved to geoId in places resolved csv.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=fbi/fbi_gov_crime/fbigovcrime_pvmap.csv --config=fbi/fbi_gov_crime/fbigovcrime_metadata.csv --output_path= <filepath/filename>`

#### Example
#### Download : 
`python3 download_script.py`

#### Processing
`python3 stat_var_processor.py --input_data=fbi/fbi_gov_crime/download_files/input_files/*.xlsx --pv_map=statvar_imports/fbi/fbi_gov_crime/fbigovcrime_pvmap.csv --config=statvar_imports/fbi/fbi_gov_crime/fbigovcrime_metadata.csv --output_path=statvar_imports/fbi/fbi_gov_crime/test_data/sample_output/fbi_gov_crime`

