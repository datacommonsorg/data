# Importing Eurostat yearly GDP into Data Commons

Author: fpernice-google

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset

> Gross Domestic Product (GDP) measures the overall level of economic activity in a country or region. Eurostat publishes various forms of economic data, including GDP, inflation, and employment. Specifically on GDP, it publishes data at various levels of government, and with different measurement styles. We import all Eurostat GDP data.

> Data Format: All considered data is measured in one of the following forms:

1. "MIO_EUR": "Million euro",
2. "EUR_HAB": "Euro per inhabitant",
3. "MIO_NAC": "Million units of national currency",
4. "MIO_PPS": "Million purchasing power standards (PPS)", or
5. "PPS_HAB": "Purchasing power standard (PPS) per inhabitant".

### Download URL

ZIP file is available for download from [here](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/nama_10r_3gdp.tsv.gz).

### License

See parent README.

### Notes and Caveats

> Eurostat also publishes these other measurement types, which are currently ignored as per tjann's request:

1. "EUR_HAB_EU": "Euro per inhabitant in percentage of the EU average",
1. "EUR_HAB_EU27_2020": "Euro per inhabitant in percentage of the EU27 (from 2020) average",
1. "MIO_PPS_EU27_2020": "Million purchasing power standards (PPS, EU27 from 2020)",
1. "PPS_EU27_2020_HAB": "Purchasing power standard (PPS, EU27 from 2020), per inhabitant",
1. "PPS_HAB_EU": "Purchasing power standard (PPS) per inhabitant in percentage of the EU average",
1. "PPS_HAB_EU27_2020": "Purchasing power standard (PPS, EU27 from 2020), per inhabitant in percentage of the EU27 (from 2020) average"

> Eurostat publishes their data with certain [flags and special values](https://ec.europa.eu/eurostat/data/database/information) that are used to mark things like breaks in time series, confidential information, estimated data, etc. These markers are currently completely filtered out of the data, and should eventually be added as extra properties on StatVarObservations.

## About the Import

### Import Artifacts

#### Cleaned Data

- [eurostat_gdp.csv](eurostat_gdp.csv).

#### Template MCFs

- [eurostat_gdp.tmcf](eurostat_gdp.tmcf).

#### StatisticalVariable Instance MCF

- [eurostat_gdp.mcf](eurostat_gdp.mcf).

#### Scripts

- [import_data.py](import_data.py): Eurostat GDP import script.

### Import Procedure

To import Eurostat GDP data, run the following command:

```
python3 import_data.py
```
