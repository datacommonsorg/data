## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [Type of place](#about-the-import)
3. [Verticals: Economy]
4. [years]
5. [how to run]

## About the Dataset
The dataset is about Uganda Health and Education adding unit and scaling factor to the variables.		

### How to download data 
Mannual download, Gone through opendata uganda portal from there selected the variables and downloaded.

### type of place:
region level

### Verticals: Economy
### years: 2011-2016

### how to run: 

Open a terminal or command prompt.
To process your data, type the following command and replace the bracketed parts with your actual file paths:
python3 stat_var_processor.py --input_data='<input csv>' --pv_map="<pv_map*.csv>"  --config="<metadata.csv>"

The script generates output in three formats: CSV, TMCF, and MCF.

