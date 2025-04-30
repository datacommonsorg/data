# EuroStat: Health Determinants based on Tobacco Consumption

## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2008,2014,2019.

The population is categorized by various set of combinations as below:
        
        1. Smoking of Tobacco Products by Sex and Educational Attainment level
        2. Smoking of Tobacco Products by Sex and Income Quintile
        3. Smoking of Tobacco Products by Sex and Degree Of Urbanisation
        4. Daily Smokers of Cigarettes by Sex and Educational Attainment level
        5. Daily Smokers of Cigarettes by Sex and Income Quintile
        6. Daily Smokers of Cigarettes by Sex and Degree Of Urbanisation
        7. Daily Exposure to Tobacco smoke indoors by Sex and Educational Attainment level
        8. Daily Exposure to Tobacco smoke indoors by Sex and Degree Of Urbanisation
        9. Smoking of Tobacco Products by Sex and Country of Birth
        10. Smoking of Tobacco Products by Sex and Country of Citizenship
        11. Former Daily Tobacco Smokers by Sex and Income Quintile
        12. Former Daily Tobacco Smokers by Sex and Educational Attainment level
        13. Duration of Daily Tobacco smoking by Sex and Educational Attainment level
        14. Use of Electronic Cigarettes or similar electronic devices by Sex and Educational Attainment level 
        15. Daily Smokers of Cigarettes by Sex and Educational Attainment level
	16. Daily Smokers of Cigarettes by Sex and Income Quintile
	17. Daily Smokers by number of Cigarettes by Sex and Educational Attainment level

#### API Output
These are the attributes that will be used
| Attribute      		                        | Description                                                   |
|-------------------------------------------------------|---------------------------------------------------------------|
| Time       					| The Year of the population estimates provided. 	                |
| Geo       					| The Area of the population estimates provided. 			|
| Tobacco Consumption  				| The type of Tobacco Consumption. 					|
| Educational Attainment level   	| The level of education of the population.  |
| Sex   				| Gender either Male or Female. 						|
| Income Quintile 				| The slab of income of the population.					|
| Degree of Urbanisation   			| The type of residence (rural/urban/semiurban) of the population.      |
| Country of Birth   				| The nativity of the population.					|
| Country of Citizenship   				| The citizenship of the population.				|
| Degree of Activity Limitation   				|  							|

#### Cleaned Data
Cleaned data will be inside [output/eurostat_population_tobaccoconsumption.csv] as a CSV file with the following columns.

- Time
- Geo
- SV
- Measurement_Method
- Observation

### Download URL
The data in tsv.gz formats are downloadable from https://ec.europa.eu/eurostat/web/main/data/database -> Data navigation tree -> Detailed datasets -> Population and social conditions -> Health -> Health determinants (hlth_det).
The actual URLs are listed in import_download_details.py

#### MCFs and Template MCFs
- [output/eurostat_population_tobaccoconsumption.mcf]
- [output/eurostat_population_tobaccoconsumption.tmcf]

### Running Tests

Run the test cases

`python3 -m unittest scripts/eurostat/health_determinants/Tobacco_consumption/process_test.py`

### Import Procedure

The below script will download the data, clean the data, Also generate final csv, mcf and tmcf files.

`python scripts/eurostat/health_determinants/Tobacco_consumption/process.py`

To download data for this import, run:

`python scripts/eurostat/health_determinants/tobacco_consumption/process.py --mode=download`

To process the downloaded data, run:

`python scripts/eurostat/health_determinants/tobacco_consumption/process.py --mode=process`

Downloaded Files are created inside 'input_files' directory.
