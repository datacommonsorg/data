# Importing the ItalySTAT: List of codes and names of territorial units into Data Commons

This directory contains artifacts required for importing the the ISTAT data into Data Commons, along with scripts used to generate these artifacts

## Artifacts:
* [Elenco-codici-statistici-e-denominazioni-al-01_01_2020_it.csv][1]: original CSV file
* [Elenco-codici-statistici-e-denominazioni-al-01_01_2020_en.csv][2]: original CSV file with column names translated into English
* [ISTAT_RegionCode_NUTS2.csv][3]: mapping from ISTAT Region Code to NUTS2 code, duplicates removed
* [ISTAT_ProvinceCode_NUTS3.csv][4]: mapping from ISTAT Province Code to NUTS3 code, duplicates removed
* [preprocess.py][5]: script for cleaning the orginal CSV files and transform into desired format of CSV files for importing into DataCommons

[1]: https://github.com/qlj-lijuan/data/blob/ISTAT/scripts/istat/geos/Elenco-codici-statistici-e-denominazioni-al-01_01_2020_it.csv
[2]: https://github.com/qlj-lijuan/data/blob/ISTAT/scripts/istat/geos/Elenco-codici-statistici-e-denominazioni-al-01_01_2020_en.csv
[3]: https://github.com/qlj-lijuan/data/blob/ISTAT/scripts/istat/geos/ISTAT_RegionCode_NUTS2.csv
[4]: https://github.com/qlj-lijuan/data/blob/ISTAT/scripts/istat/geos/ISTAT_ProvinceCode_NUTS3.csv
[5]: https://github.com/qlj-lijuan/data/blob/ISTAT/scripts/istat/geos/preprocess.py

