# Importing World Bank World Development Indicators(WDI) DATA

The primary World Bank collection of development indicators, compiled from
officially-recognized international sources. It presents the most current and
accurate global development data available, and includes national estimates.
At the moment, we only include a small subset of variables from this.
See wdi_csv2mcf for detailed data we include.

The data is from:

https://datacatalog.worldbank.org/dataset/world-development-indicators

**To generate MCFs from these files, provide the input/output paths and run:**
Download and unzip the CSV file from
https://datacatalog.worldbank.org/search/dataset/0037712 into
input_files/WDICSV.csv

Then run the command:

`python wdi_csv2mcf.py`
