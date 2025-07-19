
# Importing Google COVID-19 Mobility Data Into Data Commons

Author: @edumorlom

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

###  Import Overview

This dataset shows how visits and length of stay at different places has changed compared to a baseline every day, with the earliest data starting February 15th, 2020.
The baseline is the median value that corresponds to the day of the week during the 5-week period from January 3rd to October 15th, 2022.

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

### Source URL

The CSV file is available for download from https://www.google.com/covid19/mobility/

### Import Type: API

### Release Frequency: P1D

###  Autorefresh Type: Fully Autorefresh:
## Import Artifacts

### Raw Data
- `data.csv` gets downloaded.

### Script Execution Details
``` bash
python3 covidmobility.py
```
To run the unit tests for covidmobility.py run:
```bash
python3 -m unittest covidmobility_test.py
```

### Cleaned CSV
- `covid_mobility.csv` gets generated.

## Generating Cleaned CSV
To generate the output MCF `covid_mobility.csv`, run


