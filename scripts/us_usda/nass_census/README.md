# US Census of Agriculture Import

The Census of Agriculture, taken only once every five years, looks at land use and ownership, operator characteristics, production practices, income and expenditures.

This import includes tables 1, 48-54 from the year 2022 to the latest year Census:

* 1 - County Summary Highlights
* 48 - Hispanic, Latino, or Spanish Origin Producers
* 49 - American Indian or Alaska Native Producers
* 50 - Asian Producers
* 51 - Black or African American Producers
* 52 - Native Hawaiian or Other Pacific Islander Producers
* 53 - White Producers
* 54 - Producers Reporting More Than One Race

Source: https://www.nass.usda.gov/AgCensus/index.php

Link to the datasets:https://www.nass.usda.gov/datasets/

Individual year files will be available in the provided link.

Places: US, State, County


To generate CSV:
```
python3 process.py
```
###Automation Refresh
The process.py has a parameter 'mode' with values 'download' and 'process'

when the file 'process.py' is ran with the flag --mode=download, it will only download the files and place it in the 'input' directory.
i.e. python3 process.py mode=download

when the file 'process.py' is ran with the flag --mode=process, it will process the downloaded files and place it in the 'output' directory.
i.e. python3 process.py mode=process

when the file 'process .py' is ran without any flag, it will download and process the files and keep it in the respective directories as mentioned above.
i.e. python3 process.py

The output will be `agriculture.csv`.

The individual year outputs will also be generated as 'agriculture_{year}.csv'

To run unit tests:
```
python3 process_test.py
```
