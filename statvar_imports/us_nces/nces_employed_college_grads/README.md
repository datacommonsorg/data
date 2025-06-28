NCSES_Employed_College_Grads_Import

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an "input" folder where you should place the file to be processed.

type of place: State.

statvars: Demographics

years: 2004 to 2021.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

Command to download using the download util.

python3 download_util_script.py --download_url="https://ncses.nsf.gov/pubs/nsf23306/assets/data-tables/tables/nsf23306-tab006-002.xlsx" --output_folder="source_files" --unzip=False


#### Processing the data:


How to run:
python3 stat_var_processor.py --input_data='../../statvar_imports/us_nces/nces_employed_college_grads/test_data/<filename>.xlsx' --pv_map="../../statvar_imports/us_nces/nces_employed_college_grads/<filename>.csv" --output_path='../../statvar_imports/us_nces/nces_employed_college_grads/test_data/<filename>' --config="../../statvar_imports/us_nces/nces_employed_college_grads/<filename>.csv"



Example
python3 stat_var_processor.py --input_data='../../statvar_imports/us_nces/nces_employed_college_grads/test_data/sample_input.xlsx' --pv_map="../../statvar_imports/us_nces/nces_employed_college_grads/pv_map.csv" --output_path='../../statvar_imports/us_nces/nces_employed_college_grads/test_data/sample_output' --config="../../statvar_imports/us_nces/nces_employed_college_grads/metadata.csv"
