# US Census PEP: Population Estimate By Sex

## About the Dataset
This dataset has Population Estimates for the National, State and County geographic levels in United States from the year 1900 to latest year on a yearly basis.        

### Download URL
The data in txt/csv/xls formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables and https://www2.census.gov/programs-surveys/popest/datasets. The actual URLs are listed in download.py.

#### API Output
These are the attributes that will be used
| Attribute                                     | Description                                                   	|
|-----------------------------------------------|----------------------------------------------------------------------	|
| Year                          		| The Year of the population estimates provided.                	|
| Geo                           		| The Area of the population estimates provided.            		|
| Sex                   			| Gender either Male or Female.                         		|


#### Cleaned Data
Cleaned data will be inside [output/population_estimate_sex.csv] as a CSV file with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs
- [output/population_estimate_sex.mcf]
- [output/population_estimate_sex.tmcf]


### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/us_census/pep/us_pep_sex/process_test.py`


### Import Procedure

The below script will download the data.

`/bin/python3 scripts/us_census/pep/us_pep_sex/download.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`/bin/python3 scripts/us_census/pep/us_pep_sex/process.py`

###Automation Refresh
The process.py has a parameter 'mode' with values 'download' and 'process', and also a config_path flag to provide a json as a input file.

### Note:
The json file has to be included with the urls (only from year 1990 - 2020) that has a fake html content that escapes 200 ok status check failure.
If not provided, the url with the fake 200 ok status will be logged and the process of download gets terminated.
For the future years, the fake 200 ok status url will be logged without terminating the process of download and search for the next depreciated year. 


 ### Ways to process (with modes)
 
when the file 'process.py' is ran with the flag --mode=download, it will only download the files and put it in the input_files directory.
i.e. python3 process.py mode=download --config_path=<provide the path to skip_url.json file>

For example: --config_path=unresolved_mcf/us_census/pep/population_estimate_by_sex/skip_url.json

when the file 'process.py' is ran with the flag --mode=process, it will process the downloaded files and put it in the output directory.
i.e. python3 process.py mode=process

Note: process mode doesn't need a config_path flag

when the file 'process .py' is ran without any flag, it will download and process the files and keep it in the respective directories as mentioned above.
i.e. python3 process.py --config_path=<provide the path to skip_url.json file>

