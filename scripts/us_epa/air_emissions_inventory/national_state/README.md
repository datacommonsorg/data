# US-EPA: Air Pollutant Emissions Trends Data

## About the Dataset
This dataset has Air Pollution Emission data for the National and State geographic levels in the United States for the years 1970 to latest.

The data is categorized by geographic levels as below:
        
        1. Criteria pollutants National Tier 1 for 1970 - latest
        2. Criteria pollutants State Tier 1 for 1990 - latest


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

`sh run_tests.sh -p scripts/us_epa/air_emissions_inventory/national_state` from the data folder

or 

`python -m unittest process_test.py` from the current folder


### Import Procedure

The below script will download the data.

`python3 download.py --config_path=unresolved_mcf/us_epa/config.json`

Note on Configuration Management for Data Source URLs

To ensure consistent access to the most current data, a dedicated configuration file, config.json, will be maintained within our Google Cloud Storage (GCS) environment. This approach addresses the challenge posed by source URLs that contain dynamic and unpredictable year and date components, precluding their programmatic generation.

Content Structure:
The config.json file will adhere to a JSON array format, with each object in the array defining a download_path attribute. This attribute will contain the fully qualified URL for the latest available National and State-level data files.

The config_path parameter designates a Google Cloud Storage (GCS) location. It should be provided as the bucket and object path (e.g., my-bucket/path/to/config.json), without the gs:// prefix. The system will automatically prepend the gs:// scheme internally when accessing the resource."

Example config.json Content:

JSON

[
  {"download_path": "https://www.epa.gov/system/files/other-files/2025-04/national_tier1_caps_21feb2025.xlsx"},
  {"download_path": "https://www.epa.gov/system/files/other-files/2025-04/state_tier1_21feb2005_ktons.xlsx"}
]

Maintenance:
This configuration mechanism requires manual updates to the config.json file whenever the source URLs for the National or State data undergo revision, thereby ensuring the application always references the latest datasets.

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`python3 process.py`