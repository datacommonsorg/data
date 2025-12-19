
# Importing EPA EJSCREEN data

This directory imports data from the [EPA's EJSCREEN](https://www.epa.gov/ejscreen) - a mapping and screening tool developed by the EPA to highlight areas facing environmental justice (EJ) issues. EJSCREEN combines Census demographic data and environmental data from EPA sources. Data is organized by FIPS code and is given on the Census block level. These scripts generate the following files:

`ejscreen_airpollutants.csv`  
`ejscreen.tmcf`

which include the following StatisticalVariables:

- `Mean_Concentration_AirPollutant_DieselPM`  
- `AirPollutant_Cancer_Risk`  
- `AirPollutant_Respiratory_Hazard`  
- `Mean_Concentration_AirPollutant_Ozone`  
- `Mean_Concentration_AirPollutant_PM2.5`

which are a small subset of the available EJSCREEN variables. 

## Usage

To generate `ejscreen_airpollutants.csv` and `ejscreen.tmcf` run the following:  

    `python3 ejscreen.py`

As of July, 2021 this includes data through the end of 2020.

### Unit Tests

To run unit tests:

    `python3 -m unittest discover -v -s ../ -p "*_test.py"`

## Data Download and Documentation
https://www.epa.gov/ejscreen/download-ejscreen-data
- Since the file columns are inconsistent, we are manually checking the url, column names and add them in the config.
- Hence, setting up the import under autorefresh where the donwload congif has to be updated manually to bring new data into DataCommons 
- In the download config, attach new year with the URL and check if it exist.
- Add the suffix and filename. Refer previous years.
- Fill eht remaining dicts and also create config column list for new file.
- Update the config file in `gs://unresolved_mcf/epa/ejscreen/download_config.json` path.
