## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [Type of place](#about-the-import)
3. [Statvar](#statvar)
4. [Verticals: Demographics]
5. [years]
6. [how to run]

## About the Dataset
The data set provides selected information on national emissions of air pollutants: man-made emissions of sulphur oxides (SOx), nitrogen oxides (NOx), particulate matter (PM), carbon monoxide (CO) and volatile organic compounds (VOC). 

### How to download data 
Manual download

### type of place: Country level

### statvars:  Demographics

### years: 1990-2020

###place resolve: Manually

### how to run: 

Open a terminal or command prompt.
To process your data, type the following command and replace the bracketed parts with your actual file paths:
python3 stat_var_processor.py --input_data='<input csv>' --pv_map="<pv_map*.csv>"  --config="<metadata.csv>"  --places_resolved_csv="<place_resolver.csv>"

The script generates CSV, TMCF, & MCF files.

### Licence
License: Creative Commons Attribution


