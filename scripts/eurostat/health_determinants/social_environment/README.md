# EuroStat: Health Determinants based on Social Environment

## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2014 and 2019.

The population is categorized by various set of combinations as below:
        
        1. Overall perceived Social Support by Sex and Educational Attainment level
        2. Overall perceived Social Support by Sex and Degree of Urbanisation
        3. Persons providing informal care or assistance at least once a week by Sex and Educational Attainment level
        4. Persons providing informal care or assistance at least once a week by Sex and Degree of Urbanisation
        5. Overall perceived Social Support by Sex and Country of Birth
        6. Overall perceived Social Support by Sex and Country of Citizenship
        7. Overall perceived Social Support by Sex and Degree of Activity Limitation
       

### Download URL
The data in tsv.gz formats are downloadable from https://ec.europa.eu/eurostat/web/health/data/database -> 	Health -> Health determinants (hlth_det).
The actual URLs are listed in input_files.py.


#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| time       					| The Year of the population estimates provided. 				|
| geo       					| The Area of the population estimates provided. 				|
| Educational Attainment level   	| The level of education of the population.  |
| Sex   				| Gender either Male or Female. 							|
| Degree of Urbanisation   				| The type of residence (rural/urban/semiurban) of the population.					|
| Country of Birth   				| The nativity of the population.						|
| Country of Citizenship   				| The citizenship of the population.						|
| Degree of Activity Limitation   				|  							|




#### Cleaned Data
Cleaned data will be inside [output/eurostat_population_socialenvironment.csv] as a CSV file with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation



#### MCFs and Template MCFs
- [output/eurostat_population_socialenvironment.mcf]
- [output/eurostat_population_socialenvironment.tmcf]

### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/eurostat/health_determinants/social_environment/preprocess_test.py`




### Import Procedure

The below script will download the data and extract it.

`/bin/python3 scripts/eurostat/health_determinants/social_environment/download_input_files.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`/bin/python3 scripts/eurostat/health_determinants/social_environment/preprocess.py`