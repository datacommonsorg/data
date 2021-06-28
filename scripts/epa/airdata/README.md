# Importing EPA AirData
This directory imports [Outdoor Air Quality Data](https://aqs.epa.gov/aqsweb/airdata/download_files.html) into Data Commons. This includes mean/max concentration and AQI for Ozone, SO2, CO, NO2, PM2.5, and PM10 measured at various monitors throughout the  US, Puerto Rico and US Virgin Islands. Source CSVs are downloaded directly from the pre-generated data files.

The script generates:
- `EPA_AirQuality.csv`
- `EPA_AirQuality.tmcf`

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

## Notes on the Data
In the cleaned CSV, observations are provided on the site monitor level. For simplicity in the place mapping, we select a single monitor per site and pollutatn and provide the monitor id (POC) as airQualitySiteMonitor in the observation. So, a given observation is distinguished by observationDate, observationAbout (AirQualitySite), and measurementMethod (pollutant standard).

## Generating Artifacts
To generate `EPA_AirQuality.csv` and `EPA_AirQuality.tmcf`, run:
```
python3 air_quality.py <end_year>
```
As of June 2021, this currently includes data up to 2021.

### Running Tests
To run unit tests:
```
python3 air_quality_test.py
```
