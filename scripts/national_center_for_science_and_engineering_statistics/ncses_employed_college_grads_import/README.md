NCSES_Employed_College_Grads_Import

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an "input" folder where you should place the file to be processed.

type of place: State.

statvars: Demographics

years: 2004 to 2021.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 ../../../tools/statvar-importer/stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.csv' --pv_map='statvar_imports/NCSES_Employed_College_Grads_Import/<filename>_pvmap.csv,observationAbout:statvar_imports/NCSES_Employed_College_Grads_Import/places_resolved.csv' --config='statvar_imports/NCSES_Employed_College_Grads_Import/metadata.csv' --output_path=<filepath/filename>

Example
Download :
download_script

Processing
python3 ../../../tools/statvar-importer/stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/uae_population/test_data/7300_source_data.csv' --pv_map='data/statvar_imports/NCSES_Employed_College_Grads_Import/pvmap.csv' --config='data/statvar_imports/NCSES_Employed_College_Grads_Import/metadata.csv' --output_path=data/statvar_imports/NCSES_Employed_College_Grads_Import/test_data/output
