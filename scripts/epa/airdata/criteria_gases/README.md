# Importing EPA AirData - Criteria Gases
The script generates:
- `EPA_AirQuality_<POLLUTANT_ID>.csv`
- `EPA_AirQuality_<POLLUTANT_ID>.tmcf`

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

## Generating Artifacts 
To generate `EPA_AirQuality_<POLLUTANT_ID>.csv` and `EPA_AirQuality_<POLLUTANT_ID>.tmcf`, run: 
```
python3 generate_tmcf.py <POLLUTANT_ID>
```

### Running Tests
To run unit tests: 
```
python3 generate_tmcf_test.py
```