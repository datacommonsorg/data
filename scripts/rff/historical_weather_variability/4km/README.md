# Importing 4km Raster of RFF Weather Variability Data

This directory imports RFF's 4km rasters of weather variability data

The script generates:
- WeatherVariability_4km.csv
- WeatherVariability_4km.tmcf
- places_4km.csv
- places_4km.tcmf

and it relies on these statistic variables:
- dcs:StandardDeviation_DailyPrecipitation
- dcs:Skewness_DailyPrecipitation
- dcs:Kurtosis_DailyPrecipitation
- dcs:StandardDeviation_DailyMinTemperature
- dcs:Skewness_DailyMinTemperature
- dcs:Kurtosis_DailyMinTemperature
- dcs:StandardDeviation_DailyMaxTemperature
- dcs:Skewness_DailyMaxTemperature
- dcs:Kurtosis_DailyMaxTemperature
- dcs:HeavyPrecipitationIndex
- dcs:ConsecutiveDryDays


## Generating Artifacts:

To generate `WeatherVariability_4km.tmcf` and `WeatherVariability_4km.csv`, run:

```bash
python preprocess_4km.py
```