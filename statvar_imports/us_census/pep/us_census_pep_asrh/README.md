# USCensusPEP_AgeSexRaceHispanicOrigin Import
The script helps to downloads USCensusPEP_AgeSexRaceHispanicOrigin input data, ranging from the year 2020 up to the latest release. All downloaded files are then placed into the input_files folder

- source: https://www.census.gov/

### Download
- How to download data: We have the download script pep_asrh_download_script.py to download the data from source website and keep csv files inside the input_files folder.
### How to run:
`python3 pep_asrh_download_script.py
### Example:
`python3 pep_asrh_download_script.py'


- type of place: Country, state and county.

- statvars: Demographics

- years: 2020 to 2024 (The import covers data from 1980, as the source is now publishing only latest data (2020 onwards) we are keeping the old data(1980 - 2019) as a histoical data)


### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=data/statvar_imports/us_census/pep/us_census_pep_asrh/pep_asrh_county_pvmap.csv --config=data/statvar_imports/us_census/pep/us_census_pep_asrh/pep_asrh_metadata.csv --output_path=<filepath/filename>`

The config and pvmap files for other geo-levels are available in the same folder(us_census_pep_asrh), change the command with appropriate files to generate required output file

#### Example
#### Processing
`python3 stat_var_processor.py --input_data=input_files/county/*.csv --pv_map=pep_asrh_county_pvmap.csv --config=pep_asrh_county_metadata.csv --output_path=output/county/pep_asrh`


