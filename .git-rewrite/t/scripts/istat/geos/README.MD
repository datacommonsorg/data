# Importing the ItalySTAT: List of codes and names of territorial units into Data Commons

This directory contains artifacts required for importing the the ISTAT data into Data Commons, along with scripts used to generate these artifacts

## Artifacts:
* [raw](./raw): contains original CSV files downloaded from [ISTAT](https://www.istat.it/it/archivio/6789).
* [cleaned](./clean) csv files: 
    * [ISTAT_region.csv](./clean/ISTAT_region.csv)
    * [ISTAT_province.csv](./clean/ISTAT_province.csv)
    * [ISTAT_municipal.csv](./clean/ISTAT_municipal.csv)
* template mcfs:
    * [ISTAT_region.tmcf](./ISTAT_region.tmcf)
    * [ISTAT_province.tmcf](./ISTAT_province.tmcf)
    * [ISTAT_municipal.tmcf](./ISTAT_municipal.tmcf)
* [preprocess.py](./preprocess.py): script for cleaning the orginal CSV files and transform into desired format of CSV files for importing into DataCommons
* [test.py](./test.py): test functions for the template mcf

[1]: ./Elenco-codici-statistici-e-denominazioni-al-01_01_2020_it.csv
[2]: ./Elenco-codici-statistici-e-denominazioni-al-01_01_2020_en.csv


