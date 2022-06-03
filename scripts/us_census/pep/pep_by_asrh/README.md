# US Census PEP: Population Estimates by Age, Sex, Race and Origin

## About the Dataset
This dataset has Population Estimates for the National, State and County geographic levels in United States from the year 1980 to 2021 on a yearly basis.

The population is categorized by various set of combinations as below:
        
        1. Age, Origin.
        2. Age, Origin, Sex.
        3. Age, Origin, Race.
        4. Age, Origin, Sex and Race

### Download URL
The data in txt/csv formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables and https://www2.census.gov/programs-surveys/popest/datasets. The actual URLs are listed in file_urls.txt.


#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year       					| The Year of the population estimates provided. 				|
| Age   				| The Individual Ages or Age Buckets of the population in the US. 						|
| Race   	| Races of the population in the US.(https://www.census.gov/topics/population/race/about.html, https://www.census.gov/newsroom/blogs/random-samplings/2021/08/measuring-racial-ethnic-diversity-2020-census.html).  	|
| Sex   				| Gender either Male or Female. 							|
| Origin   		| Origin either Hispanic or Non Hispanic  		|


#### Cleaned Data
Cleaned data will be inside [output/USA_Population_ASRH.csv] as a CSV file with the following columns.

- Year
- Location
- SV
- Measurement_Method
- Count_Person



#### MCFs and Template MCFs
- [output/USA_Population_ASRH.mcf]
- [output/USA_Population_ASRH.tmcf]

### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/us_census/pep/pep_by_asrh/preprocess_test.py`




### Import Procedure

The below script will download the data.

`/bin/sh scripts/us_census/pep/pep_by_asrh/download.sh`

The below script will generate csv and mcf files.

`/bin/python3 scripts/us_census/pep/pep_by_asrh/preprocess.py`