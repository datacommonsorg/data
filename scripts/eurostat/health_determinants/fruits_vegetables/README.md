# EuroStat: Health Determinants based on Fruits And Vegetables


## About the Dataset
This dataset has Population Estimates for the National geographic levels in Europe for the years 2008,2014,2019.

The population is categorized by various set of combinations as below:
        
        1. Daily consumption of fruit and vegetables by sex and educational attainment level.
        2. Daily consumption of fruit and vegetables by sex and income quintile .
        3. Daily consumption of fruit and vegetables by sex and degree of urbanisation.
        4. Frequency of fruit and vegetables consumption by sex and educational attainment level.
        5. Frequency of fruit and vegetables consumption by sex and degree of urbanisation.
        6. Daily consumption of fruit and vegetables by sex and country of birth .
        7. Daily consumption of fruit and vegetables by sex and country of citizenship.
        8. Daily consumption of fruit and vegetables by sex and level of activity limitation.
        9. Daily consumption of fruit and vegetables by sex and body mass index . 
        10. Frequency of fruit and vegetables consumption by sex and country of birth.
        11. Frequency of fruit and vegetables consumption by sex and country of citizenship.
        12. Frequency of fruit and vegetables consumption by sex and income quintile.
        13. Frequency of fruit and vegetables consumption by sex and body mass index.
        14. Frequency of fruit and vegetables consumption by sex and level of activity limitation.
        15. Frequency of drinking sugar-sweetened soft drinks by sex and educational attainment.
        16. Frequency of drinking sugar-sweetened soft drinks by sex and body mass index.
        17. Frequency of drinking sugar-sweetened soft drinks by sex and income quintile.
        18. Frequency of drinking pure fruit or vegetable juice by sex and educational attainment.
        19. Consumption of fruits by sex and educational attainment level.
        20. Consumption of vegetables by sex and educational attainment level.
        

### Download URL
Input files are available for download from url: https://ec.europa.eu/eurostat/web/health/data/database -> Health -> Health determinants (hlth_det).

### Import Procedure
The below script will download the data and extract it.

`python scripts/eurostat/health_determinants/common/download_eurostat_input_files.py --import_name fruits_vegetables`

Files are created inside 'input_files' directory.


#### Output
Statistical variables for alcohol consumption are based on below properties available in input files.
| Attribute                                     | Description                                                       	|
|-----------------------------------------------|----------------------------------------------------------------------	|
| time                          		        | The Year of the population estimates provided.                    	|
| geo                           		        | The Area of the population estimates provided.            	    	|
| frequenc               			            | The frequency of Fruits And Vegetables.                  		        |
| Educational Attainment level      		    | The level of education of the population.  				            |
| Sex                   			            | Gender either Male or Female.                         	        	|
| Income Quintile               		        | The slab of income of the population.                 	        	|
| Degree of Urbanisation            		    | The type of residence (rural/urban/semiurban) of the population.      |
| Country of Birth                  		    | The nativity of the population.                   			        |
| Country of Citizenship                	    | The citizenship of the population.                			        |
| body mass index                               | Different BMI levels.                                                 |
| level of activity limitation                  | Different Activity.                                                   |


Below script will generate cleansed observation file (csv), mcf and tmcf files.

`python scripts/eurostat/health_determinants/fruits_vegetables/process.py`


#### Cleaned Observation File
Cleaned data will be persisted as a CSV file in output/eurostat_population_fruits_vegetables.csv with the following columns.

- time
- geo
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs File
MCF and tMCF files are presisted in below mentioned path.
- [output/eurostat_population_fruits_vegetables.mcf]
- [output/eurostat_population_fruits_vegetables.tmcf]


### Running Tests

Run the test cases

`python3 -m unittest discover -v -s scripts/eurostat/health_determinants/fruits_vegetables/ -p process_test.py`
