# US Census PEP: National Population Count

## About the Dataset
This dataset has Annual Population Estimates from the year 1900 to 2020 for different geographic level such as National, State, County, and Cities.

The population is categorized by Count_Person StatVar in Datacommons.org

https://www2.census.gov/programs-surveys/popest/tables/1900-1980/national/totals/popclockest.txt
https://www2.census.gov/programs-surveys/popest/tables/1980-1990/state/asrh/st0009ts.txt
https://www2.census.gov/programs-surveys/popest/tables/1900-1980/counties/totals/e7079co.txt
https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/co-est2020.csv


### Download URL
A backend API allows the data to be queryable and responds with txt/xls/xlsx data. The API endpoint is at "https://www2.census.gov/programs-surveys/popest/tables/1900-1980/national/totals/popclockest.txt","https://www2.census.gov/programs-surveys/popest/tables/1980-1990/state/asrh/st0009ts.txt","https://www2.census.gov/programs-surveys/popest/tables/1900-1980/counties/totals/e7079co.txt","https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/co-est2020.csv". The API takes URL as a string input and downloads the dataset.

#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year and Month   					| The Year and Month of the population estimates provided. 				|
| Resident Population   				| The total resident population in the US. 						|

#### Cleaned Data
Cleaned data will be inside [Output/USA_Annual_Population.csv] as a CSV file with the following columns.

- Year
- Location
- Count_Person[https://datacommons.org/browser/Count_Person]


#### MCFs and Template MCFs
- [Output/USA_Annual_Population.mcf]
- [Output/USA_Annual_Population.tmcf]

### Running Tests

Run the test cases

```/bin/python3 -m unittest scripts/us_census/pep/annual_population_estimate/preprocess_test.py
```


### Import Procedure

The below script will download the data
`/usr/bin/sh scripts/us_census/pep/annual_population_estimate/download.sh`

The below script will generate csv and mcf files.
`/usr/bin/python3 scripts/us_census/pep/annual_population_estimate/preprocess.py`


