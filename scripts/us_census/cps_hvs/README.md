# Importing FRED homeownership rate data into Data Commons

Author: KilimAnnejaro

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#about-the-import)
1. [Generating Artifacts](#generating-artifacts)

## About the dataset

### Download URL

The CSV file is available for download from <https://www.kaggle.com/census/homeownership-rate-time-series-collection>.

### Overview

This dataset contains two variables:
1. date: The date when the value was measured.
2. value: Count of housing units occupied by their owners as a percentage of occupied housing units. 

### License

The license is available online at <https://www.kaggle.com/census/homeownership-rate-time-series-collection>.

### Dataset Documentation and Relevant Links 

- Documentation: <https://www.kaggle.com/census/homeownership-rate-time-series-collection>
- Data Visualization UI: <https://fred.stlouisfed.org/series/MNHOWN>

## About the import

### Artifacts

#### Raw Data
- <https://github.com/datacommonsorg/data/blob/master/scripts/us_census/cps_hvs/MNHOWN.csv>: Historical homeownership rate in Minnesota.

#### Template MCF
- <https://github.com/datacommonsorg/data/blob/master/scripts/us_census/cps_hvs/Homeownership_Rate.tmcf>: TMCF for homeownership rate data.

### Import Procedure

To import new homeownership data from FRED into Data Commons, simply upload the CSVs from Kaggle, removing the _realtime_start_ and _realtime_end_ columns manually.

#### Pre-Processing Validation

To manually validate the CSV from Kaggle, download the matching CSV from the FRED at <https://fred.stlouisfed.org/series/MNHOWN> and ensure the two files contain identical information.
