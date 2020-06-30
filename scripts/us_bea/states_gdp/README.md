# Importing US Bureau of Economic Analysis quarterly GDP data per US state

## Raw Data
- Available for download at [https://www.bea.gov/data/gdp/gdp-state](https://www.bea.gov/data/gdp/gdp-state).

## Notes on Raw Data Format
- The only way of downloading the desired data from the BEA website (linked above) is by downloading relatively large Zip files. These Zip files contain lots of GDP data (e.g. GDP by industry, county, etc.), distributed across many different CSV files. In this import, we are interested in only one of these CSV files, which specifically contains quarterly GDP data per US state. Thus, in the import_data.py script outlined below, we download the entire Zip file, and pull out the single CSV file that is relevant to us.

## Cleaned Data
- [states_gdp.csv](states_gdp.csv) contains quarterly gross domestic product (GDP) data per US state as measured in three different ways:
  - **Millions of Chained 2012 dollars**: the data is inflation-adjusted to 2012 money, by using the inflation rate measured by the chain-weighted CPI (i.e., taking into account product substitutions).
  - **Millions of Current Dollars**: Nominal GDP.
  - **Quantity Index**: Percentage inflation-adjusted change in GDP with respect to the base year of 2012. For example 2015 Q2 would have a Quantity Index of 105 if it had a GDP 5% higher than the average of 2012's four quarterly GDPs after adjusting for inflation.

## Scripts
- [import_data.py](import_data.py)
  - Downloads data from the BEA website, yielding a CSV file, e.g. [states_gdp.csv](states_gdp.csv).
  - To run, call `python3 import_data.py` from the command line.
- [test_import.py](import_data.py)
  - Runs unit tests on the cleaning procedure from [import_data.py](import_data.py).
- [validate_import.py](import_data.py)
  - Validates the data extracted in [import_data.py](import_data.py). Flags any changes made to the database that could require updating the script.
