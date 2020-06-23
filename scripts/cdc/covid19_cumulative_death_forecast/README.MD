# Importing the COVID19 death forecast data from CDC
This directory contains artifacts required for importing the COVID19 death forecast data from CDC into Data Commons, along with scripts used to generate these artifacts

## Artifacts:
* [forecast_death-2020-04-13to2020-06-01.csv][1]: cleaned CSV file
* [COVID19_DeathPredictionCDC.mcf][2]: template MCF file
* [COVID19_DeathPredictionCDC_StatisticalVariable.mcf][3]: definition of StatisticalVariables
* [generate_mcf.py][4]: script used for generating the MCF files
* [preprocess.py][5]: script for cleaning the orginal CSV files and transform into desired format of CSV files for importing into DataCommons
* [CSV_original][6] : contains the original CSV files downloaded from [CDC](https://www.cdc.gov/coronavirus/2019-ncov/covid-data/forecasting-us.html)
* [utility][7] : constains files used for preprocess, generate mfcs, tests etc.

## Docs
* [Importing Doc][8]
* [Discussion on prediction data representation][9]

[1]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/forecast_death-2020-04-13to2020-06-01.csv
[2]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/COVID19_DeathPredictionCDC.mcf
[3]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/COVID19_DeathPredictionCDC_StatisticalVariable.mcf
[4]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/generate_mcf.py
[5]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/preprocess.py
[6]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/CSV_original
[7]: https://github.com/qlj-lijuan/data/tree/master/scripts/cdc/covid19_cumulative_death_forecast/utility
[8]: https://docs.google.com/document/d/12UdK2JW6vEe0bv-y5RJt_wkRKXYxmemE9lpjIdyGy88/edit?ts=5ed95c37#
[9]: https://docs.google.com/document/d/1z_ciDTnQqTWC_q6KInqCI0aMeNwHkPgI4COTRWDfl9g/edit
