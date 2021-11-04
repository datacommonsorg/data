# Importing Covid19 Wikipedia Data Into Data Commons

Author: @edumorlom

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

The import Wikipedia Pages can be found in [Config.py](./config.py).
Each page returns a time series table for a given place.

### Overview

This dataset shows how Covid-19 has impacted different Places around the world.

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


## Import Artifact

### WikidataId Map

The places' dcids are resolved by wikidataId.
Each WikidataId was queried using the following:
  1. WikiParser.get_wikidata_id() takes a Wikipedia's place URL and returns the wikidataId.
  2. NOTE: The URL has to be a real Wikipedia page, not a Template page.
  3. EXAMPLE: Given [chart](https://en.wikipedia.org/wiki/COVID-19_pandemic_in_Spain#COVID_chart), get the real name of the country from the URL (in this case "Spain"), and append it to `https://en.wikipedia.org/wiki/`.
  This will return the following `https://en.wikipedia.org/wiki/Spain`.
  4. Now that you have the URL, you can use the get_wikidata_id() with the resulting URL.

- [Config.py](Config.py)

### Output CSV

The output CSV after running the WikiParser.py script.

- [output.csv](output.csv)

### Scripts

The WikiParser script will run through all the places' URL in Config.py.
Each URL corresponds to a Wikipedia Template page, containing a single chart.
Using this table, we can generate a CSV file using Pandas.

- [WikiParser.py](WikiParser.py)

### Unit Tests

This import requires HTML pages to retrieve the data. For testing purposes, the HTML document can be found inside each tests' directory. That is, instead of accessing the Wikipedia page, the test will open a HTML document.
This is done so that the content of the table is unchanged.

- [run_tests.py](run_tests.py)

To run the unit tests, run

``` bash
python3 run_tests.py
```

## Generating CSV

To generate the output CSV `output.csv`, run

``` bash
python3 WikiParser.py
```
