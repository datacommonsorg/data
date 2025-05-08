# BLS_CES Import

- source: https://www.bls.gov/ces/ 

- how to download data: Go to https://www.bls.gov/webapps/legacy/cesbtab1.htm and select all the industries check boxes and click on "Retrieve Data".
In the new page click on "More Formatting Options" and in the "Select view of the data" field select "Multi series view" and click on "Retrieve Data", now there will be an option to download the file in xlsx

- type of place: Country.

- statvars: Economy

- years: 2015 5o 2025
### How to download the data:
`The script 'download_bls_ces.py' contains a download method which requires registered API key. Go to "https://www.bls.gov/developers/api_faqs.htm#register2" to register for the key. Save the key in config.json. config.json = {"registrationkey":<reg_key>",bls_ces_url:<url_here>"}. This json file shoud be uploaded to GCS bucket path "unresolved_mcf/us_bls/ces/latest"`



`python3 us_bls/download_bls_ces.py --place_type=<state or national> --input_folder=<output folder name> --source_folder=<source folder name>`

### How to run:
### If processing from same import folder
`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/us_bls/bls_ces/bls_ces_pvmap.csv --config=statvar_imports/us_bls/bls_ces/bls_ces_metadata.csv --output_path=<filepath/filename>`

#### Example
#### Processing
`python3 stat_var_processor.py --input_data=statvar_imports/us_bls/bls_ces/test_data/bls_ces_input.csv --pv_map=statvar_imports/us_bls/bls_ces/bls_ces_pvmap.csv --config=statvar_imports/us_bls/bls_ces/bls_ces_metadata.csv --output_path=statvar_imports/us_bls/bls_ces/test_data/bls_ces_output`
