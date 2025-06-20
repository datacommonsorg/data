NCSES_Employed_College_Grads_Import

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an "input" folder where you should place the file to be processed.

type of place: State.

statvars: Demographics

years: 2004 to 2021.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 stat_var_processor.py --input_data='/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/test_data/<filename>.xlsx' --pv_map="/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/<filename>.csv" --output_path='/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/test_data/<filename>' --config="/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/<filename>.csv"



Example
python3 stat_var_processor.py --input_data='/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/test_data/sample_input.xlsx' --pv_map="/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/pv_map.csv" --output_path='/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/test_data/sample_output' --config="/statvar_imports/national_center_for_science_and_engineering_statistics/ncses_employed_college_grads_import/metadata.csv"
