NCES_STEM_Degrees_Import
source: https://nces.ed.gov/programs/digest/d24/tables/dt24_318.45.asp

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an "source_files" folder where you should place the file to be processed. 

type of place: State.

statvars: Demographics

years: 2011 to 2021.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 ../../../tools/statvar-importer/stat_var_processor.py  --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.csv' --pv_map='statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/pvmap.csv,
--config='statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/metadata.csv' --output_path=<filepath/filename> --statvar_dcid_remap_csv='statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/dcid_remap.csv'

Example
Download :
download_script

Processing
python3 ../../../tools/statvar-importer/stat_var_processor.py  --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/test_data/nces_table_318_45.xlsx' --pv_map='data/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/pvmap.csv' --config='data/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/metadata.csv' --output_path=data/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/test_data/test_data/output



