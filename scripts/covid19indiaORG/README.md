# Importing covid19india.org Data Into Data Commons

Author: @edumorales

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

This dataset includes the total number of active cases for each region for a specific date.

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

This is further broken down into District.

## Import Artifacts

### Data APIs

The list States was auto-generated using the following script.
Simply copy and paste the script into the covid19india.org console in your preferred browser.
Top open console: Right Click >> "Inspect Element" >> "Console".

This will return a list of {State: string, ISOcode: string, API: string}

```Array.prototype.slice.call($('select').childNodes).map(node => {const isoCode = JSON.parse(node.value)['stateCode']; return {"State": node.label, "ISOcode": isoCode, "API": `https://api.covid19india.org/v4/min/timeseries-${isoCode}.min.json`}})```

- [Config.py](Config.py)

### India wikidataId Map

The places' dcids are resolved by wikidataId.
The map of State->District->wikidataId was generated using the following:
    1. The wikidataId for each place is queried using the place_resolver.go script.
    2. A script is used against wikidata.org/wiki/${wikidataId} that verifies that the place is both a District and part of India.
    3. Manual check has been performed to ensure that the name matches.

- [INDIA_MAP.py](INDIA_MAP.py)

### Output CSV

The output CSV after running the Covid19IndiaORG script.

- [output.csv](output/output.csv)

### Scripts

The Covid19IndiaORG script will call the covid19india.org API for each state in Config.py.
The covid19india.org APIs return return a JSON keyed by districtName->date.
Using this JSON, we can generate a CSV file using Pandas.

- [Covid19IndiaORG.py](Covid19IndiaORG.py)

### Unit Tests

This import requires API calls to retrieve the data, for testing purposes, the JSON data will can be found inside each tests' directory. That is, instead of making an API call, the test will open the JSON file and treat its content as the API response.

- [run_tests.py](run_tests.py)

To run the unit tests, run

``` bash
python3 run_tests.py
```

## Generating CSV

To generate the output CSV `output.csv`, run

``` bash
python3 main.py
```
