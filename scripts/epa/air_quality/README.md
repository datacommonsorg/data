# Importing EPA Air Quality Data
This directory imports [Outdoor Air Quality Data](https://aqs.epa.gov/aqsweb/documents/data_api.html) into Data Commons. This includes the daily concentration and AQI for various air pollutants at various monitoring sites throughout the US, Puerto Rico, and US Virgin Islands. 

The script generates:
- `EPA_AirQuality.csv`
- `EPE_AirQuality.tmcf`

and relies on the following StatisticalVariables:
- Mean_Concentration_AirPollutant_Ozone
- Max_Concentration_AirPollutant_Ozone
- AirQualityIndex_AirPollutant_Ozone
- Mean_Concentration_AirPollutant_SO2 
- Max_Concentration_AirPollutant_SO2 
- AirQualityIndex_AirPollutant_SO2
- Mean_Concentration_AirPollutant_CO
- Max_Concentration_AirPollutant_CO 
- AirQualityIndex_AirPollutant_CO
- Mean_Concentration_AirPollutant_NO2
- Max_Concentration_AirPollutant_NO2 
- AirQualityIndex_AirPollutant_NO2
- Mean_Concentration_AirPollutant_PM2.5
- Max_Concentration_AirPollutant_PM2.5 
- AirQualityIndex_AirPollutant_PM2.5
- Mean_Concentration_AirPollutant_PM10 
- Max_Concentration_AirPollutant_PM10 
- AirQualityIndex_AirPollutant_PM10

## Data Caveats
- When using the AQS API to retrieve data, sometimes multiple pollutant standards can be returned for a pollutant. This import uses a single standard for each pollutant. The selected standards are the most recent (in terms of year), and in some cases, those which provided AQI. These standards also match those used in the [pre-generated data files](https://aqs.epa.gov/aqsweb/airdata/download_files.html). These include: 
    - Ozone 8-hour 2015
    - SO2 1-hour 2010
    - CO 8-hour 1971
    - NO2 1-hour
    - PM25 24-hour 2012
    - M10 24-hour 2006

## Generating Artifacts 
To generate `EPA_AirQuality.csv` and `EPE_AirQuality.tmcf`, run: 
```
python3 generate_tmcf.py
```