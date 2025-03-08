
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

#Downloading and Processing Data
To perform "download and process", run the below command: python3 ejscreen.py Running this command generates input_fles and csv, mcf, tmcf files

If you want to perform "only process", run the below command: python3 ejscreen.py --mode=process

If you want to perform "only download", run the below command: python3 ejscreen.py --mode=download

### Unit Tests

To run unit tests:

    `python3 -m unittest discover -v -s ../ -p "*_test.py"`

## Data Download and Documentation
https://www.epa.gov/ejscreen/download-ejscreen-data
