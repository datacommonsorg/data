# India Air Quality Data - 2012 to 2022

This import contains mean values of various pollutants measured once in 4 hours along with other details like station name, state, city, and date for the period of 2012-2022.

## About the dataset
Air Quality Data for the years 2012 to 2022. Available in [Central Pollution Control Board portal](https://app.cpcbccr.com/AQI_India/).

Source: Central Pollution Control Board (CPCB), Ministry of Environment, Forests, and Climate Change. Dataset description can be found in [this PDF](https://app.cpcbccr.com/ccr_docs/FINAL-REPORT_AQI_.pdf)

### Steps done to map stations names to district LGD codes
1. Google Maps API is used to get the lat-long coordinates for each station. The search query contained station name, city name and state name.
2. The lat-long values are queried against the India districts shapefile to get district names. This will provide the district in which a particular coordinate exists.
3. The district names are mapped to LGD codes using the data from [LGD website](https://lgdirectory.gov.in/globalviewdistrictforcitizen.do).

## Overview
Consistent values of Air Quality Data for most of the stations are available from 2012-2022. The earliest available data for each station might vary depending on when the station is published. The zip file for the year wise raw data can be found in [India_AQI.zip (Mediafire repository)](https://download843.mediafire.com/3dc0vasoeqpg/fe619iz4gnxfgg3/India_AQI.zip). 

The codes used for scraping CPCB's data are taken from [National Air Quality Index - India - cpcbccr data scraping](https://github.com/thejeshgn/cpcbccr)

The cleaned csv has the following columns:

- Year: Corresponding year of the date at which the pollutant readings were recorded
- City: Corresponding city in which the pollutant readings were recorded
- Site_name: The name of the station
- State: Corresponding state in which the pollutant readings were recorded
- Date: The date on which pollutant readings were recorded. (ISO Format)\
- dcid: a unique string to identify a station
- LgdCode: District code
- PM25: Mean PM2.5 reading (spanning across 4 hours) of a given station
- PM10: Mean PM10 reading (spanning across 4 hours) of a given station
- NO2: Mean Nitrogen Dioxide reading (spanning across 4 hours) of a given station
- NH3: Mean Ammonia reading (spanning across 4 hours) of a given station
- SO2: Mean Sulfur Dioxide reading (spanning across 4 hours) of a given station
- CO: Mean Carbon Monoxide reading (spanning across 4 hours) of a given station
- O3: Mean Ozone reading (spanning across 4 hours) of a given station
- AT: Mean Atmospheric Temperature reading (spanning across 4 hours) of a given station
- BP: Mean Barometric Pressure reading (spanning across 4 hours) of a given station
- SR: Mean Surface Radiation / Solar Insulation reading (spanning across 4 hours) of a given station
- RH: Mean Relative Humidity reading (spanning across 4 hours) of a given station
- WD: Mean Wind Direction reading (spanning across 4 hours) of a given station
- NO: Mean Nitrogen Monoxide reading (spanning across 4 hours) of a given station
- NOx: Mean readings (spanning across 4 hours) of family of Nitrogen oxides of a given station
- Benzene: Mean Benzene reading (spanning across 4 hours) of a given station
- Toluene: Mean Toluene reading (spanning across 4 hours) of a given station
- Xylene: Mean Xylene reading (spanning across 4 hours) of a given station
- MP_Xylene: Mean Meta-Xylene reading (spanning across 4 hours) of a given station
- Eth_Benzene: Mean Ethyl Benzene reading (spanning across 4 hours) of a given station

### TMCF
- [India_AQI.tmcf](./India_AQI.tmcf)

### MCF
- [India_AQI.mcf](./India_AQI.mcf)

### Scripts
- [preprocess.py](./preprocess.py): Cleans up data and generates the cumulative CSV file

## Script usage
Execute the following command from `scripts/` directory to generate the necessary csv, mcf and tmcf files:

```
python -m india_aqi.preprocess
```
        
