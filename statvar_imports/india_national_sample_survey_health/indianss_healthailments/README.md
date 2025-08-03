IndiaNSS_HealthAilments
source: https://ndap.niti.gov.in/dataset/7300

how to download data: Download script (download_script.py). To download the data, you'll need to use the provided download script,download_script.py. This script will automatically create an "input" folder where you should place the file to be processed. The script also requires a configuration file (config.ini) to function correctly.

type of place: State.

statvars: Demographics

years: 2004 to 2005.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.csv' --pv_map='statvar_imports/IndiaNSS_HealthAilments/<filename>_pvmap.csv,observationAbout:statvar_imports/IndiaNSS_HealthAilments/places_resolved.csv' --config='statvar_imports/IndiaNSS_HealthAilments/metadata.csv' --output_path=<filepath/filename>

Example
Download :
download_script

Processing
python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/uae_population/test_data/7300_source_data.csv' --pv_map='data/statvar_imports/IndiaNSS_HealthAilments/pvmap.csv' --config='data/statvar_imports/IndiaNSS_HealthAilments/metadata.csv' --output_path=data/statvar_imports/IndiaNSS_HealthAilments/test_data/output
