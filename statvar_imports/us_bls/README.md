### How to download the data:
`The script 'download_bls_ces_data.py' contains a download method which requires registered API key. Go to "https://www.bls.gov/developers/api_faqs.htm#register2" to register for the key. Save the key in config.json. config.json = {"registrationkey":<reg_key>",bls_ces_url:<url_here>"}. This json file shoud be uploaded to GCS bucket path "unresolved_mcf/us_bls/ces/latest"`


`python3 us_bls/download_bls_ces_data.py --place_type=<state or national> --input_folder=<output folder name> --source_folder=<source folder name>`

### Example
`python3 us_bls/download_bls_ces_data.py --place_type=state --input_folder=bls_ces_state/state_folder --source_folder=source_folder`