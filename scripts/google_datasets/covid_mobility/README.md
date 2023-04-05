
# Importing Google COVID-19 Mobility Data Into Data Commons

Author: @edumorlom

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

The CSV file is available for download from https://www.google.com/covid19/mobility/

### Overview

This dataset shows how visits and length of stay at different places has changed compared to a baseline every day, with the earliest data starting February 15th, 2020.
The baseline is the median value that corresponds to the day of the week during the 5-week period from January 3rd to February 6th, 2020.

This data set is divided into six headline stats:

#### Grocery & Pharmacy
This dataset includes mobility trends for grocery markets, food warehouses, farmers markets, specialty food shops, drug stores and pharmacies.
#### Park
This dataset includes mobility trends for local parks, national parks, public beaches, marinas, dog parks, plazas, and public gardens.
#### TransportHub
This dataset includes mobility trends for public transportation hubs.
#### Retail & Recreation
This dataset includes mobility trends for restaurants, cafes, shopping centers, theme parks, museums, libraries, and movie theaters.
#### Residence
This dataset includes mobility trends for places of residence.
#### Workplace
This dataset includes mobility trends for places of work.


The entire dataset is broken down into:

#### Country
This is further broken down into Area/State/County.
Date
Type of Place

## Import Artifacts

### Raw Data
- `data.csv` gets downloaded.

### MCF
- `covid_mobility_output.mcf` gets generated.

### Scripts
- [CovidMobility.py](CovidMobility.py)
- [TestCovidMobility.py](TestCovidMobility.py)

### Notes
The geoIds of the U.S Counties was generated using the County's real FIPS code from:
https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697

For example, Miami-Dade County would be geoId/12086 because Miami-Dade's FIPS code is 12086.
The USDA website above lists only the unique part of the name, that is "Miami-Dade" instead of "Miami-Dade County".

The words ["County", "Parish", "Borough"] were appended to all names except those that were Cities, Parishes or Boroughs.

Some counties have two different keys that map to the same value/geoId, though.
For example:

{
    "De Kalb County": "geoId/17037",
    "DeKalb County": "geoId/17037"
}

The reason for this is because the Google Mobility dataset uses an alternative name to refer to the same region.
Any modifications to the names were duplicated.

## Generating MCF
To generate the output MCF `covid_mobility_output.mcf`, run

``` bash
python3 covidmobility.py
```

To run the unit tests for CovidMobility.py run:

```bash
python3 TestCovidMobility.py
```
