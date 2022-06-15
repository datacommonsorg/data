# Importing County-Level RFF Weather Variability Data

This directory imports RFF's county-level weather variability data

The script generates:
- WeatherVariability_Counties.csv
- WeatherVariability_Counties.tmcf

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

To generate `WeatherVariability_Counties.tmcf` and `WeatherVariability_Counties.csv`, run:

```bash
python preprocess_csv.py
```