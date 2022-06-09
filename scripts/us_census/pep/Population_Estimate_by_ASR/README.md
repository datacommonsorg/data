# US Census PEP: Population Estimates by Age, Sex and Race

## About the Dataset
This dataset has Population Estimates for the National, State and County geographic levels in United States from the year 1900 to 2020 on a yearly basis.

The population is categorized by various set of combinations as below:
        
        1. Age, Sex.
        2. Age, Race.
        3. Age, Sex, Race.

### Download URL
The data in txt/csv formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables and https://www2.census.gov/programs-surveys/popest/datasets. The actual URLs are listed in national/state/county JSON files.


#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year       					| The Year of the population estimates provided. 				|
| Age   				| The Individual Ages or Age Buckets of the population in the US. 						|
| Race   	| Races of the population in the US (https://www.census.gov/topics/population/race/about.html, https://www.census.gov/newsroom/blogs/random-samplings/2021/08/measuring-racial-ethnic-diversity-2020-census.html).  	|
| Sex   				| Gender either Male or Female. 							|



#### Cleaned Data
Cleaned data will be inside [output/usa_population_asr.csv] as a CSV file with the following columns.

- Year
- geo_ID
- SVs
- Measurement_Method
- observation



#### MCFs and Template MCFs
- [output/usa_population_asr.mcf]
- [output/usa_population_asr.tmcf]

### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/us_census/pep/Population_Estimate_by_ASR/process_test.py`




### Import Procedure

The below script will download the data and clean the data, Also generate final csv, mcf and tmcf files.

`/bin/python3 scripts/us_census/pep/Population_Estimate_by_ASR/process.py`
