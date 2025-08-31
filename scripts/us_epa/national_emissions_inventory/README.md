# US-EPA: National Air Pollutant Emissions Data

## About the Dataset
This dataset has Air Pollution Emission data for the County and Tribal geographic levels in the United States for the years 2008 to 2017.


### Download URL
The data in zip formats are downloadable from https://www.epa.gov/air-emissions-inventories/national-emissions-inventory-nei.
The actual URLs are listed in download_config.py.


### API Output
These are the attributes that we will use
| Attribute      				| Description                                               |
|-------------------------------|-----------------------------------------------------------|
| dataset       					| The Year of the emission estimates provided. 				|
| fips code     					| The Area of the emission estimates provided. 				|
| scc   	        | Source from where the pollution is emitted.               |
| pollutant code   				    | The Gas generated which pollutes the Air. 			    |
| pollutant type(s)   				    | The type of Gas generated which pollutes the Air. 			    |

### Cleaned Data
Cleaned data will be inside [output/national_emissions.csv] as a CSV file with the following columns.

- year
- geo_Id
- SV
- Measurement_Method
- observation
- unit


### MCFs and Template MCFs
- [output/national_emissions.mcf]
- [output/national_emissions.tmcf]


### Running Tests

Run the test cases

`run_tests.sh -p scripts/us_epa/national_emissions_inventory`


### Import Procedure

The below script will download the data.

point - `python3 download_input_files.py point`
nonpoint - `python3 download_input_files.py nonpoint`
onroad - `python3 download_input_files.py onroad`
nonroad(default) - `python3 download_input_files.py nonroad`
all - `python3 download_input_files_all.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`python3 process.py`