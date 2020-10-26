
# Importing covid19india.org Data Into Data Commons

Author: @edumorlom

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

The import APIs can be found in ./Config.py.
Each API returns the time series data for each Indian State along with the State's districts.

### Overview

This dataset shows how Covid-19 has impacted States and Districts in India.
#### Active Cases
This dataset includes the total number of cumulative active cases for each region for a specific date.
#### Recovered Cases
This dataset includes the total number of cumulative recovered cases for each region for a specific date.
#### Total Cases
This dataset includes the total number of cumulative total cases for each region for a specific date. This is Active Cases + Recovered Cases.
#### Deaths
This dataset includes the total number of cumulative deaths for each region for a specific date.
#### Tested
This dataset includes the total number of tests performed for each region for a specific date.


The entire dataset is broken down into:
#### State
This is further broken down into:
#### District


## Import Artifacts

### Data APIs
- [Config.py](Config.py)

### India wikidataId Map
- [INDIA_MAP.py](INDIA_MAP.py)

### Output CSV
- [output.mcf](output/output.csv)

### Scripts
- [main.py](main.py)

### Notes
The places' dcids are resolved by wikidataId.
The wikidataId for each place was found using the place_resolver.go as well as so manual checks.

## Generating MCF
To generate the output CSV `output.csv`, run

``` bash
python3 main.py
```
