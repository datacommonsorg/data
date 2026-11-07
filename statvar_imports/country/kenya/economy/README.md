## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [Type of place](#about-the-import)
3. [Statvar](#statvar)
4. [Verticals: Economy]
5. [years]
6. [how to run]

## About the Dataset
The data set describes about the economy in Kenya country. 

### How to download data 
Went through the website https://kenya.opendataforafrica.org/ selected the variables manually and downloaded.

### type of place: State level

### statvars:  Economy

### years: 2013-2020

###place resolve: Manually

### how to run: 

Open a terminal or command prompt.
To process your data, type the following command and replace the bracketed parts with your actual file paths:
python3 stat_var_processor.py --input_data='<input csv>' --pv_map="<pv_map*.csv>"  --config="<metadata.csv>"  --

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=statvar_imports/country/kenya/economy/sample_input/<input_file>.csv --pv_map=statvar_imports/country/kenya/economy/pv_map/_pvmap.csv --config=statvar_imports/country/kenya/economy/pv_map/.csv --output_path=statvar_imports/country/kenya/economy/test_data/sample_output/

The script generates CSV, TMCF, & MCF files.



