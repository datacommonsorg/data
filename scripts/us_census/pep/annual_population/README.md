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

Note:
The json file has to be included with the urls (only from year 1990 - 2020) that has a fake html content that escapes 200 ok status check failure. If not provided, the url with the fake 200 ok status will be logged and the process of download gets terminated. For the future years, the fake 200 ok status url will be logged without terminating the process of download and search for the next depreciated year.

Ways to process (with modes)
when the file 'preprocess.py' is ran with the flag --mode=download, it will only download the files and put it in the input_files directory. i.e. python3 process.py mode=download --config_path=

For example: --config_path=unresolved_mcf/us_census/pep/annual_population/skip_url.json

when the file 'prprocess.py' is ran with the flag --mode=process, it will process the downloaded files and put it in the output directory. i.e. python3 process.py mode=process

Note: process mode doesn't need a config_path flag

when the file 'preprocess .py' is ran without any flag, it will download and process the files and keep it in the respective directories as mentioned above. i.e. python3 process.py --config_path=
