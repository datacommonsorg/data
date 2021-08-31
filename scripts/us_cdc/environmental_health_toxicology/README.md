## Importing CDC Air Quality and Precipitation Index Data
Author: Samantha Piekos @spiekos and Padma Gundapaneni @padma-g

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [License](#license)
    5. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)

## About the Dataset

### Download URL
The air quality data can be downloaded from [the CDC website](https://data.cdc.gov/browse?category=Environmental+Health+%26+Toxicology&sortBy=last_modified&page=1).

The precipitation index data can be downloaded from the following links:
* [Palmer Drought Severity Index](https://data.cdc.gov/Environmental-Health-Toxicology/Palmer-Drought-Severity-Index-1895-2016/en5r-5ds4)
* [Standardized Precipitation Evapotranspiration Index](https://data.cdc.gov/Environmental-Health-Toxicology/Standardized-Precipitation-Evapotranspiration-Inde/6nbv-ifib)
* [Standardized Precipitation Index](https://data.cdc.gov/Environmental-Health-Toxicology/Standardized-Precipitation-Index-1895-2016/xbk2-5i4e)

All the downloaded data is in .csv format. 

### Overview
The air quality data comes from the CDC and the EPA. The datasets contain "modeled predictions of PM2.5 and ozone levels from the EPA's Downscaler model". According to the CDC, "these data are used by the CDC's National Environmental Public Health Tracking Network to generate air quality measures."

The precipitation index data comes from the CDC and the Cooperative Institute for Climate and Satellites. The datasets contain "monthly Standardized Precipitation Evapotranspiration Index (SPEI) data from 1895-2016 provided by the Cooperative Institute for Climate and Satellites - North Carolina". According to the CDC, "these data are used by the CDC's National Environmental Public Health Tracking Network to generate drought measures."

In this effort, we imported the census tract-level and county-level PM2.5 and ozone level data for the years 2001-2016. We also imported at the county level the Palmer Drought Severity Index (PDSI) for years 1895-2016, the Standardized Precipitation Evapotranspiration Index (SPEI) for years 1895-2016, and the Standardized Precipitation Index (SPI) for years 1895-2016.

Among the air quality datasets, census tract-level datasets contain estimates of the mean predicted concentration and associated standard error, while county-level datasets contain estimates of the mean predicted concentration, the median predicted concentration, the maximum predicted concentration, and the population-weighted predicted concentration.

The precipitation index datasets contain precipitation index data for a given year, month, and county.

### Notes and Caveats

None.

### License
The data is made available for public-use by the [CDC](https://www.cdc.gov/nchs/data_access/ftp_data.htm). Users of CDC National Center for Health Statistics Data must comply with the CDC's [data use agreement](https://www.cdc.gov/nchs/data_access/restrictions.htm).

### Dataset Documentation and Relevant Links
These data were collected as part of the [CDC National Environment Public Health Tracking Network](https://ephtracking.cdc.gov/). The documentation for the air quality datasets is accessible [here](https://www.cdc.gov/nceh/tracking/topics/AirQuality.htm). The documentation for the drought data sets is accessible [here](https://www.cdc.gov/nceh/tracking/topics/Drought.htm).

## About the Import

### Air Quality Artifacts

#### Scripts
[`parse_air_quality.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/scripts/parse_air_quality.py)

[`parse_air_quality_test.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/scripts/parse_air_quality_test.py)

#### Test Files
[`Ozone_Daily_Census_Tract_test_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/test_files/Ozone_Daily_Census_Tract_test_file.csv)

[`Ozone_Daily_Census_Tract_test_file_expected_output.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/test_files/Ozone_Daily_Census_Tract_test_file_expected_output.csv)

[`Ozone_Daily_County_test_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/test_files/Ozone_Daily_County_test_file.csv)

[`Ozone_Daily_County_test_file_expected_output.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/test_files/Ozone_Daily_County_test_file_expected_output.csv)

[`PM2.5_Concentrations_Daily_Census_Tract_test_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/test_files/PM2.5_Concentrations_Daily_Census_Tract_test_file.csv)

[`PM2.5_Concentrations_Daily_Census_Tract_test_file_expected_output.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/test_files/PM2.5_Concentrations_Daily_Census_Tract_test_file_expected_output.csv)

#### tMCFs
[`OzoneCensusTractPollution.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/tMCFs/OzoneCensusTractPollution.tmcf)

[`OzoneCountyPollution.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/air_quality/tMCFs/environmental_health_toxicology/air_quality/tMCFs/OzoneCountyPollution.tmcf)

[`PM25CensusTractPollution.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/air_quality/environmental_health_toxicology/air_quality/tMCFs/PM25CensusTractPollution.tmcf)

[`PM25CountyPollution.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/air_quality/tMCFs/PM25CountyPollution.tmcf)

### Precipitation Artifacts

#### Script
[`parse_precipitation_index.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/scripts/parse_precipitation_index.py)

[`parse_precipitation_index_test.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/scripts/parse_precipitation_index_test.py)

#### Test Files
[`Palmer_Drought_Severity_Index_test_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/test_files/Palmer_Drought_Severity_Index_test_file.csv)

[`Palmer_Drought_Severity_Index_test_file_expected_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/test_files/Palmer_Drought_Severity_Index_test_file_expected_file.csv)

[`Standardized_Precipitation_Evapotranspiration_Index_test_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/test_files/Standardized_Precipitation_Index_test_file.csv)

[`Standardized_Precipitation_Evapotranspiration_Index_test_file_expected_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/test_files/Standardized_Precipitation_Evapotranspiration_Index_test_file_expected_file.csv)

[`Standardized_Precipitation_Index_test_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/test_files/Standardized_Precipitation_Evapotranspiration_Index_test_file.csv)

[`Standardized_Precipitation_Index_test_file_expected_file.csv`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/test_files/precipitation/Standardized_Precipitation_Index_test_file_expected_file.csv)

#### tMCFs
[`PalmerDroughtSeverityIndex.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/tMCFs/PalmerDroughtSeverityIndex.tmcf)

[`StandardizedPrecipitationEvapotranspirationIndex.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/tMCFs/StandardizedPrecipitationEvapotranspirationIndex.tmcf)

[`StandardizedPrecipitationIndex.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/environmental_health_toxicology/precipitation/tMCFs/StandardizedPrecipitationIndex.tmcf)

### Import Procedure

#### Testing

`@input_file` - path to the test input csv file to be cleaned

`@expected_output_file` - path to cleaned csv file with the expected output

To test the air quality data cleaning script, run from the directory containing the test files:

```bash
$ python3 parse_air_quality_test.py input_file expected_output_file
```

To test the precipitation index data cleaning script, run from the directory containing the test files:

```bash
$ python3 parse_precipitation_index_test.py input_file expected_output_file
```

#### Processing Steps

`@input_file` - path to the input csv file to be cleaned

`@output_file` - path to write the cleaned csv file

To clean the air quality data files, run:

```bash
$ python3 parse_air_quality.py input_file output_file
```


To clean the precipitation index data files, run: 

```bash
$ python3 parse_precipitation_index.py input_file output_file
```
