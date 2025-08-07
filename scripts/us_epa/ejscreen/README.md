
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

To add a new year of data, you must update the config.json file.

1. Update Core Configuration
First, add the new year to the YEARS array. Next, specify the exact column names for that year in the CSV_COLUMNS_BY_YEAR object. You also need to provide the filename for the uncompressed CSV in FILENAMES and the name of the compressed file in ZIP_FILENAMES. Finally, if the new year's data is located in a different web directory, update the URL_SUFFIX accordingly.

2. Handle Column Renaming
If the column names in the new year's file do not match the standardized schema (e.g., ID is used instead of ID_New), you must add the year to the RENAME_COLUMNS_YEARS array. Then, create a mapping in the RENAME_COLUMNS_BY_YEAR object, which instructs the script on how to rename the raw column headers to the standardized names. This step is crucial for maintaining data consistency across all years.


To generate `ejscreen_airpollutants.csv` and `ejscreen.tmcf` run the following:  

#Downloading and Processing Data
To perform "download and process", run the below command: python3 ejscreen.py Running this command generates input_fles and csv, mcf, tmcf files

If you want to perform "only process", run the below command: python3 ejscreen.py --mode=process

If you want to perform "only download", run the below command: python3 ejscreen.py --mode=download

### Unit Tests

To run unit tests:

    `python3 -m unittest discover -v -s ../ -p "*_test.py"`

## Data Download and Documentation
https://www.epa.gov/ejscreen/download-ejscreen-data
