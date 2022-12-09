# US-EPA: Air Pollutant Emissions Trends Tier 1 Data
About the Dataset
This dataset has Air Pollution Emission data for the National, State and County geographic levels in the United States for the years 2008, 2011, 2014, 2017.

## Download URL
The data in csv formats are downloadable from https://www.epa.gov/air-emissions-inventories. The actual URLs are listed in download.sh.

### API Output
These are the attributes that we will use

Attribute	Description
| Attribute                                     | Description                                                   	|
|-----------------------------------------------|----------------------------------------------------------------------	|
| year                          		| The year of the emission estimates provided.              	  	|
| geo_ID                           		| The area of the emission estimates provided.            		|
| Source Category                   		| Source from where the pollution is emitted.                      	|
| Pollutant                   			| The gas generated which pollutes the Air.                      	|

#### Cleaned Data
Cleaned data will be inside [output/airpollution_emission_trends_county_tier1.csv] as a CSV file with the following columns.

- year
- geo_Id
- SV
- measurement_method
- observation

#### MCFs and Template MCFs
[output/airpollution_emission_trends_county_tier1.mcf]
[output/airpollution_emission_trends_county_tier1.tmcf]


#### Running Tests
Run the test cases
`run_tests.sh -p scripts/us_epa/air_emissions_inventory/county`

#### Import Procedure
- To download the data and generate the required output:

1. `python3 download.sh`
This script will generate a folder input_html_files which will contain .html files for all the four year.

2. `python3 download.py`
This script will generate a folder input_iles containing data files for all the four year in .csv format.

3. `python3 process.py`
This script will clean the data, also generate final csv, mcf and tmcf files.
