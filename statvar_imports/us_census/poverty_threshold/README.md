## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [Type of place](#about-the-import)
3. [Verticals: Economy]
4. [years]
5. [how to run]

## About the Dataset
Poverty Threshold by United States Census Bureau it describes the weighted average thresholds in Current Population Survey Annual Social and Economic Supplement (CPS ASEC).		

### How to download data 
Mannual download
Gone through open data portal, selected the variables and downloaded manually

### type of place:
country level

### Verticals: Economy
### years: 2010-2023

### how to run: 

Open a terminal or command prompt.
To process your data, type the following command and replace the bracketed parts with your actual file paths:
python3 stat_var_processor.py --input_data='<input csv>' --pv_map="<pv_map*.csv>"  --config="<metadata.csv>"

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=statvar_imports/us_census/poverty_threshold/sample_input/<input_file>.csv --pv_map=statvar_imports/us_census/poverty_threshold/pv_map/_pvmap.csv --config=statvar_imports/us_census/poverty_threshold/pv_map/.csv --output_path=statvar_imports/us_census/poverty_threshold/test_data/sample_output/

The script generates output in three formats: CSV, TMCF, and MCF.

