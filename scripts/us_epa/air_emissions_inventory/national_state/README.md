# US-EPA: Air Pollutant Emissions Trends Data

## About the Dataset
This dataset has Air Pollution Emission data for the National and State geographic levels in the United States for the years 1970 to 2021.

The data is categorized by geographic levels as below:
        
        1. Criteria pollutants National Tier 1 for 1970 - 2021
        2. Criteria pollutants State Tier 1 for 1990 - 2021


### Download URL
The data in xlsx formats are downloadable from https://www.epa.gov/air-emissions-inventories/air-pollutant-emissions-trends-data.
The actual URLs are listed in download.py.


#### API Output
These are the attributes that we will use
| Attribute      				| Description                                               |
|-------------------------------|-----------------------------------------------------------|
| year       					| The Year of the emission estimates provided. 				|
| geo_ID      					| The Area of the emission estimates provided. 				|
| Source Category   	        | Source from where the pollution is emitted.               |
| Pollutant   				    | The Gas generated which pollutes the Air. 			    |


#### Cleaned Data
Cleaned data will be inside [output/airpollution_emission_trends_tier1.csv] as a CSV file with the following columns.

- year
- geo_Id
- SV
- Measurement_Method
- observation


#### MCFs and Template MCFs
- [output/airpollution_emission_trends_tier1.mcf]
- [output/airpollution_emission_trends_tier1.tmcf]


### Running Tests

Run the test cases

`run_tests.sh -p scripts/us_epa/air_emissions_inventory/national_state`


### Import Procedure

The below script will download the data.

`python3 download.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`python3 process.py`