# US-EPA: National Air Pollutant Emissions Data

### Import Overview
This dataset has Air Pollution Emission data for the County and Tribal geographic levels in the United States for the years 2008 to 2020.

### Download URL/source URL
The data in zip formats are downloadable from https://www.epa.gov/air-emissions-inventories/national-emissions-inventory-nei.
The actual URLs are listed in download_config.py.

### Import Type 
API Download

### Source Data Availability
The EPA's National Emissions Inventory (NEI) data, found at https://www.epa.gov/air-emissions-inventories/national-emissions-inventory-nei, is typically released in a comprehensive form every three years. While some point source data is collected annually, the full national inventory is a triennial publication.

### Release Frequency:
EPA NEI data updates every three years

### Autorefresh Type 
    Fully Autorefresh 

### Script Execution Details
The below script will download the data.
`python3 download.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.
`python3 process.py`

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


