# US Census PEP: National Population Count

## About the Dataset
This dataset has Annual Population Estimates from the year 1900 to 2021 for different geographic level such as National, State, County, and Cities.

The population is categorized by [Count_Person](https://datacommons.org/browser/Count_Person) StatVar in Datacommons.org

### Download URL
The data in txt/csv formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables and https://www2.census.gov/programs-surveys/popest/datasets. The actual URLs are listed in input_url.json.

#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year and Month   					| The Year and Month of the population estimates provided. 				|
| Population Estimates  				| The total population estimates in the US/State/County/City.						|


#### Cleaned Data
Cleaned data will be inside [output_files/usa_annual_population.csv] as a CSV file with the following columns.

- Year
- Location
- [Count_Person](https://datacommons.org/browser/Count_Person)


#### MCFs and Template MCFs
- [output_files/usa_annual_population.mcf]
- [output_files/usa_annual_population.tmcf]

### Running Tests

Run the test cases

`python3 scripts/us_census/pep/annual_population/preprocess_test.py`

### Import Procedure

The below script will download the data, generate csv, mcf and tmcf files.

`python3 scripts/us_census/pep/annual_population/preprocess.py`

To download data, run:

`python3 scripts/us_census/pep/annual_population/preprocess.py` --mode=download

To process data, run:

`python3 scripts/us_census/pep/annual_population/preprocess.py` --mode=process

Downloaded files will be inside 'scripts/us_census/pep/annual_population/input_files' directory and output will be generated on 'scripts/us_census/pep/annual_population/output_files' directory.

