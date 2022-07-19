# EuroStat: Health Determinants based on BMI

## About the Dataset
This dataset has US Tract Transportation Statistics for Household for years 2009,2017.

The population is categorized by various set of combinations as below:
        
        1. PersonMiles, PersonTrips, VehicleMiles, VehicleTrips
        2. PersonMiles with Houshold combination
        3. PersonTrips with Houshold combination
        4. VehicleMiles with Houshold combination
        5. VehicleTrips with Houshold combination

### Download URL
The data in csv, zip formats are downloadable from https://www.bts.dot.gov/latch/latch-data -> 	By Census Tract (CSV) for 2017 year, By Census Tract (CSV) for 2009 year.

The actual URLs are listed in download_input_files.py.


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

The below script will download the data and saves to local folder **input_files**.

`/bin/python3 scripts/eurostat/health_determinants/bmi/download_input_files.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`/bin/python3 scripts/eurostat/health_determinants/bmi/process.py`