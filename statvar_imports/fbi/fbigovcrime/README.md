# FBIGovCrime Import

- source: https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads 

- how to download data: Download script (fbigovcrime_downlod_script.py).
    Manually downloaded  XLSX files from the source and uploaded to our GCS bucket.Process.py is used to pre process the xlxs files.

- type of place: City.

- statvars: Crime

- years: 2020 to 2023

- place_resolution: Places resolved to geoId in places resolved csv(statvar_imports/fbi/fbigovcrime/fbigovcrime_places_resolved.csv)).

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=data/statvar_imports/fbi/fbigovcrime/fbigovcrime_pvmap.csv --config_file=data/statvar_imports/fbi/fbigovcrime/fbigovcrime_metadata.csv --output_path= <filepath/filename>`

#### Example
#### Download : 
`python3 fbigovcrime_downlod_script.py`

#### Processing
If processing from current import folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=download_folder/input_files/* --config_file=fbigovcrime_metadata.csv --output_path=output/fbi_gov_crime`

Semi Autorefresh:
Upload final files to:

     * `gs://unresolved_mcf/fbi/city/latest`
Trigger `data/import-automation/executor/run_import.sh` manually for test/prod ingestion 


