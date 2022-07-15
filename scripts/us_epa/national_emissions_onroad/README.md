# US-EPA: National Air Pollutant Emissions OnRoad Data

## About the Dataset
This dataset has Air Pollution Emission data for the County and Tribal geographic levels in the United States for the years 2008 to 2017.


### Download URL
The data in zip formats are downloadable from https://www.epa.gov/air-emissions-inventories/national-emissions-inventory-nei.
The actual URLs are listed in download.py.


#### API Output
These are the attributes that we will use
| Attribute      				| Description                                               |
|-------------------------------|-----------------------------------------------------------|
| dataset       					| The Year of the emission estimates provided. 				|
| fips code     					| The Area of the emission estimates provided. 				|
| scc   	        | Source from where the pollution is emitted.               |
| pollutant code   				    | The Gas generated which pollutes the Air. 			    |
| pollutant type(s)   				    | The type of Gas generated which pollutes the Air. 			    |

#### Cleaned Data
Cleaned data will be inside [output/airpollution_emission_trends_tier1.csv] as a CSV file with the following columns.

- year
- geo_Id
- SV
- Measurement_Method
- observation
- unit


#### MCFs and Template MCFs
- [output/national_emission_onroad.mcf]
- [output/national_emission_onroad.tmcf]


### Running Tests

Run the test cases

`python3 -m unittest process_test.py`


### Import Procedure

The below script will download the data.

`python3 download.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`python3 process.py`