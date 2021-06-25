# Importing EPA AirData - Criteria Gases
The script generates:
- `EPA_CriteriaGases.csv`
- `EPA_CriteriaGases.tmcf`

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

## Notes on the Data
In the cleaned CSV, observations are provided on the site level. Sometimes a site can have multiple monitors, but for simplicity in the place mapping, we select the first observation for a monitor and provide the monitor id (POC) as airQualitySiteMonitor in the AirQualitySite. So, a given observation is distinguished by observation_date, observation_about (AirQualitySite), and measurementMethod (pollutant standard).

## Generating Artifacts
To generate `EPA_CriteriaGases.csv` and `EPA_CriteriaGases.tmcf`, run:
```
python3 criteria_gases.py
```

### Running Tests
To run unit tests:
```
python3 criteria_gases_test.py
```
