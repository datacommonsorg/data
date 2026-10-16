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

The below script will download the data:

`python3 download.py --config_path=unresolved_mcf/us_epa/config.json`

#### Configuration Management & Automatic Fallback for Data Source URLs

To access the latest data, a configuration file (`config.json`) is stored in Google Cloud Storage (GCS) at `gs://unresolved_mcf/us_epa/config.json`. Because the EPA periodically publishes revised National and State `.xlsx` workbooks with new release-date suffixes (retiring the older URLs with HTTP 404), `download.py` uses a two-tier resolution strategy:

1. **Primary (GCS Config)**: Reads `download_path` entries from `--config_path` (passed as `bucket_name/path/to/config.json` without the `gs://` prefix) and verifies that all configured URLs return HTTP 200.
2. **Automatic Fallback (Live EPA Trends Page Discovery)**: If the GCS config cannot be read or any configured URL returns a non-200 status (such as HTTP 404 after an EPA release update), `download.py` automatically scrapes `https://www.epa.gov/air-emissions-inventories/air-pollutant-emissions-trends-data` to discover and validate the current `national_tier1_caps*.xlsx` and `state_tier1*ktons.xlsx` URLs.

Current `config.json` Content (`gs://unresolved_mcf/us_epa/config.json`):

```json
[
  {"download_path": "https://www.epa.gov/system/files/other-files/2026-09/national_tier1_caps_04sep2026.xlsx"},
  {"download_path": "https://www.epa.gov/system/files/other-files/2026-09/state_tier1_1990_2025_04sep2026_ktons.xlsx"}
]
```
*(When the EPA publishes a newer release on the [Air Pollutant Emissions Trends Data](https://www.epa.gov/air-emissions-inventories/air-pollutant-emissions-trends-data) page, `download.py` automatically discovers the updated URLs if `config.json` has not yet been updated.)*

#### Processing

The below script cleans the downloaded workbooks and generates the final CSV, MCF, and TMCF files:

`python3 process.py`