NCES_STEM_Degrees_Import
source: https://nces.ed.gov/programs/digest/d24/tables/dt24_318.45.asp

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an input_files folder. where you should place the file to be processed. 

type of place: State.

statvars: Demographics

years: 2011 to 2021.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 stat_var_processor.py  --input_data='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/test_data/<filename>.xlsx' --pv_map='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/<filename>.csv' --config='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/<filename>.csv' --output_path='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/test_data /<filename>' --statvar_dcid_remap_csv='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/<filename>.csv'


`If the Statistical Variable (SV) requires remapping, include the flag --statvar_dcid_remap_csv in above command.
--statvar_dcid_remap_csv='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/dcid_remap.csv'

Example

Processing
python3 stat_var_processor.py --input_data='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/test_data/sample_input.xlsx' --pv_map='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/pvmap.csv' --config='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/metadata.csv' --output_path='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/test_data/sample_output' --statvar_dcid_remap_csv='/statvar_imports/us_steam_degrees_data/nces_stem_degrees_import/dcid_remap.csv'



