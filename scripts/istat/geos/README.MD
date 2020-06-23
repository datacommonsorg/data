# Importing the ItalySTAT: List of codes and names of territorial units into Data Commons

This directory contains artifacts required for importing the the ISTAT data into Data Commons, along with scripts used to generate these artifacts

## Artifacts:
* [Elenco-codici-statistici-e-denominazioni-al-01_01_2020_it.csv][1]: original CSV file
* [Elenco-codici-statistici-e-denominazioni-al-01_01_2020_en.csv][2]: original CSV file with column names translated into English
* [preprocess.py](./preprocess.py): script for cleaning the orginal CSV files and transform into desired format of CSV files for importing into DataCommons
* cleaned csv file: 
    -[ISTAT_region.csv](./ISTAT_region.csv)
    -[ISTAT_province.csv](./ISTAT_province.csv)
    -[ISTAT_municipal.csv](./ISTAT_municipal.csv)
* template mcfs:
     -[ISTAT_region.tmcf](./ISTAT_region.tmcf)
     -[ISTAT_province.tmcf](./ISTAT_province.tmcf)
     -[ISTAT_municipal.tmcf](./ISTAT_municipal.tmcf)

[1]: ./Elenco-codici-statistici-e-denominazioni-al-01_01_2020_it.csv
[2]:./Elenco-codici-statistici-e-denominazioni-al-01_01_2020_en.csv


