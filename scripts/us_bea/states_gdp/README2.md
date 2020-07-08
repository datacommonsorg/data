# Importing US Bureau of Economic Analysis quarterly GDP data per US state into Data Commons

Author: fpernice-google

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

ZIP file is available for download from [https://www.bea.gov/data/gdp/gdp-state](https://www.bea.gov/data/gdp/gdp-state).

### Overview

> Gross Domestic Product (GDP) measures the overall level of economic activity in a country or region. The US Department of Commerce’s Bureau of Economic Analysis (BEA) publishes various forms of economic data, including GDP, consumer spending, income and saving, prices, inflation, and employment. Specifically on GDP, it publishes data at the national, state, industry and county levels, among others. In this import, we focus on overall US state GDP data, as well as per industry per US state GDP.

> Data Format: All considered data is measured in either 2012 chained US Dollars or current US Dollars. The former means that the data is inflation-adjusted to 2012 money, by using the inflation rate measured by the chain-weighted CPI (i.e. taking into account product substitutions). The latter simply means nominal GDP. In both cases, during the cleaning process, this data gets converted from millions of USD to USD (i.e. by multiplying by one million).

This dataset is broken up into 2 major families of variables:
1. US state GDP: Quarterly GDP per US state.
2. US state industry GDP: Quarterly GDP per industry in each US State.

US state GDP is further broken down into:
1. Chained 2012 USD: GDP measured in chained 2012 USD.
2. Nominal USD: GDP measured in nominal (current) USD.

US state industry GDP is further broken down into:
1. Industry code 11: Agriculture, forestry, fishing and hunting.
2. Industry code 21: Mining, quarrying, and oil and gas extraction
3. Industry code 22: Utilities
4. Industry code 23: Construction
5. Industry code 31_33: Manufacturing
6. Industry code 321&327_339: Durable goods manufacturing
7. Industry code 311_316&322_326: Nondurable goods manufacturing
8. Industry code 42: Wholesale trade
9. Industry code 44_45: Retail trade
10. Industry code 48_49: Transportation and warehousing
11. Industry code 51: Information
12. Industry code 52: Finance and insurance
13. Industry code 53: Real estate and rental and leasing
14. Industry code 54: Professional, scientific, and technical services
15. Industry code 55: Management of companies and enterprises
16. Industry code 56: Administrative and support and waste management and remediation services
17. Industry code 61: Educational services
18. Industry code 62: Health care and social assistance
19. Industry code 71: Arts, entertainment, and recreation
20. Industry code 72: Accommodation and food services
21. Industry code 81: Other services (except government and government enterprises)


### Notes and Caveats

- The only way of downloading the desired data from the BEA website (linked above) is by downloading relatively large Zip files. These Zip files contain lots of GDP data (e.g. GDP by industry, county, etc.), distributed across many different CSV files. In this import, we are interested in only one of these CSV files, which specifically contains quarterly GDP data per US state. Thus, in the import_data.py script outlined below, we download the entire Zip file, and pull out the single CSV file that is relevant to us.

- In the case of per industry data, some industries in some states are so small that the data had to he excluded from the database for privacy reasons. In the raw data, these datapoints are marked as "(D)" for "Disclosure Avoidance," and are cleaned out during data processing.=

### Dataset Documentation and Relevant Links

- Documentation: [https://www.bea.gov/resources/methodologies/gdp-by-state](https://www.bea.gov/resources/methodologies/gdp-by-state).
- Data Visualization UI: [https://apps.bea.gov/itable/iTable.cfm?ReqID=70&step=1#reqid=70&step=1&isuri=1](https://apps.bea.gov/itable/iTable.cfm?ReqID=70&step=1#reqid=70&step=1&isuri=1).

#### Cleaned Data
- [states_gdp.csv](states_gdp.csv): US state GDP data.
- [states_industry_gdp.csv](states_industry_gdp.csv): Per US state per industry GDP data.

#### Template MCFs
- [states_gdp.tmcf](states_gdp.tmcf): US state GDP TMCF.
- [states_industry_gdp.tmcf](states_industry_gdp.tmcf): Per US state per industry GDP TMCF.

#### StatisticalVariable Instance MCF
- [states_gdp_statvars.mcf](states_gdp_statvars.mcf): US state GDP MCF.
- [states_gdp_industry_statvars.mcf](states_gdp_industry_statvars.mcf): Per US state per industry GDP MCF.

#### Scripts
- [states_gdp_statvars.mcf](states_gdp_statvars.mcf): US state GDP MCF.
- [states_gdp_industry_statvars.mcf](states_gdp_industry_statvars.mcf): Per US state per industry GDP MCF.

### Import Procedure

To import US state GDP data, run the following command:
```
python3 import_data.py
```
To import US state per industry GDP data, run the following command:
```
python3 import_industry_data_and_gen_mcf.py
```
