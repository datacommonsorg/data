# EuroStat: Health Determinants based on Social Environment


## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2014,2019.

The population is categorized by various set of combinations as below:
        
        1. Overall perceived social support by sex and educational attainment level.
        2. Overall perceived social support by sex and degree of urbanisation .
        3. Persons providing informal care or assistance at least once a week by sex and educational attainment level.
        4. Persons providing informal care or assistance at least once a week by sex and degree of urbanisation.
        5. Overall perceived social support by sex and country of birth .
        6. Overall perceived social support by sex and country of citizenship .
        7. Overall perceived social support by sex and level of activity limitation.
        

### Download URL
Input files are available for download from url: https://ec.europa.eu/eurostat/web/health/data/database -> Health -> Health determinants (hlth_det).

### Import Procedure
The below script will download the data and extract it.

`python scripts/eurostat/health_determinants/common/download_eurostat_input_files.py --import_name social_environment`

Files are created inside 'input_files' directory.


#### Output
Statistical variables for alcohol consumption are based on below properties available in input files.
| Attribute                                     | Description                                                   	|
|-----------------------------------------------|----------------------------------------------------------------------	|
| time                          		| The Year of the population estimates provided.                	|
| geo                           		| The Area of the population estimates provided.            		|
| Social Environment  				| The type of Social Environment.                        		|
| Educational Attainment level      		| The level of education of the population.  				|
| Sex                   			| Gender either Male or Female.                         		|
| Degree of Urbanisation            		| The type of residence (rural/urban/semiurban) of the population.      |
| Country of Birth                  		| The nativity of the population.                   			|
| Country of Citizenship                	| The citizenship of the population.                			|
| Level of Activity Limitation               	| Different Activity.                                                   |


Below script will generate cleansed observation file (csv), mcf and tmcf files.

`python scripts/eurostat/health_determinants/social_environment/process.py`


#### Cleaned Observation File
Cleaned data will be persisted as a CSV file in output/eurostat_population_social_environment.csv with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs File
MCF and tMCF files are presisted in below mentioned path.
- [output/eurostat_population_social_environment.mcf]
- [output/eurostat_population_social_environment.tmcf]


### Running Tests

Run the test cases

`python3 -m unittest discover -v -s scripts/eurostat/health_determinants/social_environment/ -p process_test.py`