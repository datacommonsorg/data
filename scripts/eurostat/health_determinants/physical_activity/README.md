# EuroStat: Health Determinants based on Physical Activity

## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2008,2014,2019.

The population is categorized by various set of combinations as below:
        
        1. Health-Enhancing Physical Activity by Sex and Educational Attainment level
        2. Health-Enhancing Physical Activity by Sex and Income Quintile
        3. Health-Enhancing Physical Activity by Sex and Degree of Urbanisation
        4. Work-Related Physical Activity by Sex and Educational Attainment level
        5. Work-Related Physical Activity by Sex and Income Quintile
        6. Work-Related Physical Activity by Sex and Degree of Urbanisation
        7. NonWork-Related Physical Activity by Sex and Educational Attainment level
        8. NonWork-Related Physical Activity by Sex and Income Quintile
        9. NonWork-Related Physical Activity by Sex and Degree of Urbanisation
        10. Health-Enhancing NonWork-Related Physical Activity by Sex and Educational Attainment level
        11. Health-Enhancing NonWork-Related Physical Activity by Sex and Income Quintile
        12. Health-Enhancing NonWork-Related Physical Activity by Sex and Degree of Urbanisation
        13. Health-Enhancing Physical Activity by Sex and Country of Birth
        14. Health-Enhancing Physical Activity by Sex and Country of Citizenship
        15. Health-Enhancing Physical Activity by Sex and Degree of Activity Limitation
        16. Health-Enhancing NonWork-Related Physical Activity by Sex and BMI
        17. Daily Physical Activity by Sex and Educational Attainment level
        

### Download URL
The data in tsv.gz formats are downloadable from https://ec.europa.eu/eurostat/web/main/data/database -> Data navigation tree -> Detailed datasets -> Population and social conditions -> Health -> Health determinants (hlth_det).
The actual URLs are listed in import_download_details.py


#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| time       					| The Year of the population estimates provided. 				|
| geo       					| The Area of the population estimates provided. 				|
| Physical Activity   				| The type of Physical Activity. 						|
| Educational Attainment level   	| The level of education of the population.  |
| Sex   				| Gender either Male or Female. 							|
| Income Quintile 				| The slab of income of the population.						|
| Degree of Urbanisation   				| The type of residence (rural/urban/semiurban) of the population.					|
| Country of Birth   				| The nativity of the population.						|
| Country of Citizenship   				| The citizenship of the population.						|
| Degree of Activity Limitation   				|  							|


#### Cleaned Data
Cleaned data will be inside [output/eurostat_population_physicalactivity.csv] as a CSV file with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs
- [output/eurostat_population_physicalactivity.mcf]
- [output/eurostat_population_physicalactivity.tmcf]

### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/eurostat/health_determinants/physical_activity/process_test.py`


### Import Procedure

The below script will download the data, clean the data, Also generate final csv, mcf and tmcf files.

`python scripts/eurostat/health_determinants/physical_activity/process.py`

To download data for this import, run:

`python scripts/eurostat/health_determinants/physical_activity/process.py --mode=download`

To process the downloaded data, run:

`python scripts/eurostat/health_determinants/physical_activity/process.py --mode=process`

Downloaded Files are created inside 'input_files' directory.
