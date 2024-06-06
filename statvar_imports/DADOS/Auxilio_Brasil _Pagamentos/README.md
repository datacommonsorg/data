## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [Type of place](#about-the-import)
3. [Statvar](#statvar)
4. [Verticals: Demographics]
5. [years]
6. [how to run]

## About the Dataset
Auxílio Brasil is a Brazilian government program that provides financial aid to low-income families.
### How to download data 

### type of place:
Data is available at the Municipality level.
    
### statvars: 
'dcid:Count_Person_AuxílioBrasil' represents the number of individuals who are recipients of the Auxílio Brasil program.
'dcid:Amout_Person_AuxílioBrasil' represents the total amount of financial assistance distributed through the Auxílio Brasil program.

### Verticals: Demographics
### years: 2021-2023

### how to run: 
# Step 1.
This Python script helps you split large monthly files into smaller files for each municipality. Update the input_file path with the location of your specific file before running the script.
```
python3 brazilSplit.py
```
The script creates folders for the output files. These folders will have the same names as the corresponding input files. Then places all the generated output files within these newly created folders 

# step 2
place resolve :

The place_resolve.txt file having  all the sed commands for place resolution. Update the file path in the place_resolve.txt and then run it from your terminal.


# step 3
How to run: 
Open a terminal or command prompt.
To process your data, type the following command and replace the bracketed parts with your actual file paths:
python3 stat_var_processor.py --input_data='<input csv>' --pv_map="<pv_map*.csv>"  --config="<metadata.csv>"

The script generates output in three formats: CSV, TMCF, and MCF.

### Licence
