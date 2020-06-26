# Importing US Bureau of Economic Analysis quarterly GDP data per US state

## Cleaned Data
- [states_gdp.csv](states_gdp.csv) contains quarterly gross domestic product (GDP) data per US state as measured in three different ways:
 - **Millions of Chained 2012 dollars**: the data is inflation-adjusted to 2012 money, by using the inflation rate measured by the chain-weighted CPI (i.e., taking into account product substitutions).
 - **Millions of Current Dollars**: Nominal GDP.
 - **Quantity Index**: Percentage inflation-adjusted change in GDP with respect to the base year of 2012. For example 2015 Q2 would have a Quantity Index of 105 if it had a GDP 5% higher than the average of 2012's four quarterly GDPs after adjusting for inflation.

## Scripts
- [import_data.py](import_data.py)
  - Downloads data from the BEA website, yielding a CSV file, e.g. [states_gdp.csv](states_gdp.csv).
