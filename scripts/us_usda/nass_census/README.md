# US Census of Agriculture Import

The Census of Agriculture, taken only once every five years, looks at land use and ownership, operator characteristics, production practices, income and expenditures.

This import includes tables 1, 48-54 for the 2017 Census:

* 1 - County Summary Highlights
* 48 - Hispanic, Latino, or Spanish Origin Producers
* 49 - American Indian or Alaska Native Producers
* 50 - Asian Producers
* 51 - Black or African American Producers
* 52 - Native Hawaiian or Other Pacific Islander Producers
* 53 - White Producers
* 54 - Producers Reporting More Than One Race

Source: https://www.nass.usda.gov/AgCensus/index.php

Places: US, State, County

The source data is currently in `https://storage.cloud.google.com/datcom-csv/usda/2017_cdqt_data.txt`.

To generate CSV:
```
python3 process.py
```

The output will be `agriculture.csv`.

To run unit tests:
```
python3 process_test.py
```
