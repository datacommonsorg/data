# EuroStat: Health Determinants based on Alcohol Consumption


## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2008,2014,2019.

The population is categorized by various set of combinations as below:
        
        1. Alcohol Consumption by Sex and Educational Attainment level.
        2. Alcohol Consumption by Sex and Income Quintile.
        3. Alcohol Consumption by Sex and Degree Of Urbanisation.
        4. Binge Drinking by Sex and Educational Attainment level.
        5. Binge Drinking by Sex and Income Quintile.
        6. Binge Drinking by Sex and Degree Of Urbanisation.
        7. Hazardous Alcohol Consumption by Sex and Educational Attainment level.
        8. Hazardous Alcohol Consumption by Sex and Degree Of Urbanisation.
        9. Hazardous Alcohol Consumption by Degree Of Urbanisation. 
        10. Alcohol Consumption by Sex and Country of Birth.
        11. Alcohol Consumption by Sex and Country of Citizenship.
        
#### Output
Statistical variables for alcohol consumption are based on below properties available in input files.
| Attribute                                     | Description                                                   	|
|-----------------------------------------------|----------------------------------------------------------------------	|
| time                          		| The Year of the population estimates provided.                	|
| geo                           		| The Area of the population estimates provided.            		|
| frequent               			| The frequency of Alcohol Consumption.                  		|
| Educational Attainment level      		| The level of education of the population.  				|
| Sex                   			| Gender either Male or Female.                         		|
| Income Quintile               		| The slab of income of the population.                 		|
| Degree of Urbanisation            		| The type of residence (rural/urban/semiurban) of the population.      |
| Country of Birth                  		| The nativity of the population.                   			|
| Country of Citizenship                	| The citizenship of the population.                			|


#### Cleaned Observation File
Cleaned data will be persisted as a CSV file in output/eurostat_population_alcohol_consumption.csv with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs File
MCF and tMCF files are presisted in below mentioned path.
- [output/eurostat_population_alcohol_consumption.mcf]
- [output/eurostat_population_alcohol_consumption.tmcf]

### Download URL

The data in tsv.gz formats are downloadable from https://ec.europa.eu/eurostat/web/main/data/database -> Data navigation tree -> Detailed datasets -> Population and social conditions -> Health -> Health determinants (hlth_det).
The actual URLs are listed in import_download_details.py

### Running Tests

Run the test cases

`python3 -m unittest discover -v -s scripts/eurostat/health_determinants/alcohol_consumption/ -p process_test.py`

### Import Procedure

The below script will download the data, clean the data, Also generate final csv, mcf and tmcf files.

`python scripts/eurostat/health_determinants/alcohol_consumption/process.py`

To download data for this import, run:

`python scripts/eurostat/health_determinants/alcohol_consumption/process.py --mode=download`

To process the downloaded data, run:

`python scripts/eurostat/health_determinants/alcohol_consumption/process.py --mode=process`

Downloaded Files are created inside 'input_files' directory.


