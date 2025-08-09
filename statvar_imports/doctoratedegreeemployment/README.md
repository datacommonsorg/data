
NCSES_DoctorateDegreeEmployment
description: "Science,engineering and health doctorate holders employed in universities and 4-year colleges by broad occupation,sex,race,ethnicity and tenure status"

source: https://ncses.nsf.gov/pubs/nsf19304/assets/data/tables/wmpd19-sr-tab09-026.xlsx

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an input_files folder. where you should place the file to be processed. 

type of place: State.

statvars: Demographics

years: 2017

place_resolution: Places resolved to wikidataId in metadata sheet itself.


Command to download using the download util.

python3 download_script.py  --output_folder="source_files" --unzip=False


#### Processing the data:


How to run:
python3 stat_var_processor.py  --input_data='../../statvar_imports/doctoratedegreeemployment/test_data/<filename>.xlsx' --pv_map='../../statvar_imports/doctoratedegreeemployment/<filename>.csv' --config='../../statvar_imports/doctoratedegreeemployment/<filename>.csv' --output_path='../../statvar_imports/doctoratedegreeemployment/test_data /<filename>'


Example

Processing
python3 stat_var_processor.py --input_data='../../statvar_imports/doctoratedegreeemployment/test_data/sample_input.csv' --pv_map='../../statvar_imports/doctoratedegreeemployment/pv_map.csv' --config='../../statvar_imports/doctoratedegreeemployment/metadata.csv' --output_path='../../statvar_imports/doctoratedegreeemployment/test_data/sample_output'


