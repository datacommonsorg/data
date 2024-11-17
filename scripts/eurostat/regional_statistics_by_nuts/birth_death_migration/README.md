# Importing Eurostat "Demographic balance and crude rates" into Data Commons

Author: jinpz

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset

This dataset contains demographic balance and change stats:

- Birth event counts and crude rates
- Mortality event counts and crude rates
- Migration events and crude rates

Data is available at the NUTS3 level and above.

### Download URL

ZIP file is available for download from [here](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_gind3/?format=TSV&compressed=true).


### License

See parent README.

### Notes and Caveats

> Currently, this import does not import:

1. "NATGROW": "Natural change of population",
1. "CNMIGRAT": "Net migration plus statistical adjustment",
1. "NATGROWRT": "Crude rate of natural change of population",
1. "CNMIGRART": "Crude rate of net migration plus statistical adjustment",

> Eurostat publishes their data with certain [flags and special values](https://ec.europa.eu/eurostat/data/database/information) that are used to mark things like breaks in time series, confidential information, estimated data, etc. These markers are currently completely filtered out of the data, and should eventually be added as extra properties on StatVarObservations.

## About the Import

### Import Artifacts

#### Cleaned Data

- [EurostatNUTS3_BirthDeathMigration.csv](EurostatNUTS3_BirthDeathMigration.csv).

#### Template MCFs

- [EurostatNUTS3_BirthDeathMigration.tmcf](EurostatNUTS3_BirthDeathMigration.tmcf).

#### StatisticalVariable Instance MCF

- [EurostatNUTS3_BirthDeathMigration_statvar.mcf](EurostatNUTS3_BirthDeathMigration_statvar.mcf).

#### Scripts

- [import_data.py](import_data.py): import script.
- [import_data_test.py](import_data_test.py): import testing script.

### Import Procedure

This script offers three modes of operation: download, process, or both download and process.
To import data, run the following command:

```
1. Download and Process (python3 import_data.py or no mode flag):

2. Download Only (python3 import_data.py --mode=download):

3. Process Only (python3 import_data.py --mode=process):

```

### Testing Procedure

How to Create Sample Data: Extract a subset of rows from your source input file to generate sample input and output CSV files.

To test import procedure, run the following command:

```
python3 import_data_test.py

```
