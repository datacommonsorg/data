# EuroStat: Health Determinants based on BMI

## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2008,2014,2019.

The population is categorized by various set of combinations as below:
        
        1. BMI by Sex and Educational Attainment level
        2. BMI by Sex and Income Quintile
        3. BMI by Sex and Degree of Urbanisation
        4. BMI by Sex and Country of Birth
        5. BMI by Sex and Country of Citizenship
        6. BMI by Sex and Degree of Activity Limitation
        
Dataset with Educational Attainment level and Income Quintile provides data for 2008, 2014, and 2019.

Dataset with Degree of Urbanisation, Country of Birth, Country of Citizenship and Degree of Activity Limitation provides data for 2014 only.


### Download URL
The data in tsv.gz formats are downloadable from https://ec.europa.eu/eurostat/web/main/data/database -> Data navigation tree -> Detailed datasets -> Population and social conditions -> Health -> Health determinants (hlth_det).
The actual URLs are listed in import_download_details.py


#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| time       					| The Year of the population estimates provided. 				|
| geo       					| The Area of the population estimates provided. 				|
| bmi                           | Different BMI levels
| Educational Attainment level   	| The level of education of the population.  |
| Sex   				| Gender either Male or Female. 							|
| Income Quintile 				| The slab of income of the population.						|
| Degree of Urbanisation   				| The type of residence (rural/urban/semiurban) of the population.					|
| Country of Birth   				| The nativity of the population.						|
| Country of Citizenship   				| The citizenship of the population.						|
| Degree of Activity Limitation   				|  Different Activity Levels							|


#### Cleaned Data
Cleaned data will be inside [output_files/eurostat_population_bmi.csv] as a CSV file with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs
- [output_files/eurostat_population_bmi.mcf]
- [output_files/eurostat_population_bmi.tmcf]

### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/eurostat/health_determinants/bmi/process_test.py`


### Import Procedure

The below script will download the data, clean the data, Also generate final csv, mcf and tmcf files.

`python scripts/eurostat/health_determinants/bmi/process.py`

To download data for this import, run:

`python scripts/eurostat/health_determinants/bmi/process.py --mode=download`

To process the downloaded data, run:

`python scripts/eurostat/health_determinants/bmi/process.py --mode=process`

Downloaded Files are created inside 'input_files' directory.
