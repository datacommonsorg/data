# US EIA: Form 860 Data Import

This folder includes scripts to download and process the annual Form 860 dataset: https://www.eia.gov/electricity/data/eia860/

The survey collects generator-level specific information about existing and planned generators and associated environmental equipment at electric power plants with 1 megawatt or greater of combined nameplate capacity in the United States. Summary level data can be found in the [Electric Power Annual](https://www.eia.gov/electricity/annual/).

This dataset is published annually since 2001 (with an earlier version from 1990-2000). For this import, we will focus on 2019.

The data is available as a series of Excel spreadsheets.

## Run

To download and process the data:
```bash
python3 -m main
```
This generates *.csv in this folder which can be used for the import, along with the accompanying *.mcf and *.tmcf.

At the moment, this only processes Schedule 1: Utility and Schedule 2: Power Plants.

To run tests:
```bash
python3 -m unittest main_test.py
```