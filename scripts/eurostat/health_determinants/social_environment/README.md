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
The data in tsv.gz formats are downloadable from https://ec.europa.eu/eurostat/web/main/data/database -> Data navigation tree -> Detailed datasets -> Population and social conditions -> Health -> Health determinants (hlth_det).
The actual URLs are listed in import_download_details.py


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


### Import Procedure

The below script will download the data, clean the data, Also generate final csv, mcf and tmcf files.

`python scripts/eurostat/health_determinants/social_environment/process.py`

To download data for this import, run:

`python scripts/eurostat/health_determinants/social_environment/process.py --mode=download`

To process the downloaded data, run:

`python scripts/eurostat/health_determinants/social_environment/process.py --mode=process`

Downloaded Files are created inside 'input_files' directory.