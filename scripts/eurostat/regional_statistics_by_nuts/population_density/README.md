# Importing EuroStat Population Density Into Data Commons

Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset

This dataset has the population density (per square kilometer) for European Union (EU) countries down to their NUTS3 geos, according to the (NUTS2013-NUTS2016) classification. It has population density for the years of [1990-2018].

The original dataset is broken up into 3 major families of variables:

1. Date: Years from 1990 to 2018 with some holes in time series marked with note "b" in the original dataset
2. unit,geo: e.g. PER_KM2,AL
3. value: population density which is person count per square kilometer, some with note "e"="estimated"

unit,geo is further broken down into:

1. unit: person per KM2
2. geo: NUTS3 codes for regions of Europe

### Download URL

[TSV] file is available for [download](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_d3dens/?format=TSV&compressed=true).

### License

See parent README.

### Dataset Documentation and Relevant Links

- Documentation: <https://ec.europa.eu/eurostat/cache/metadata/en/demo_r_gind3_esms.htm>

### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"
- There are estimated values in the original dataset. Note =”e”
- As written, we're importing the estimated values as regular values.

## About the Import

### Artifacts

#### Cleaned Data

[PopulationDensity_Eurostat_NUTS3.csv](./PopulationDensity_Eurostat_NUTS3.csv)

The cleaned csv has the columns:

1. Date: Subset of years from 1990 to 2018 with values in the original dataset
2. GeoID: NUTS3 codes
3. Count_Person_PerArea: float values

#### Template MCFs

[PopulationDensity_Eurostat_NUTS3.tmcf](./PopulationDensity_Eurostat_NUTS3.tmcf)

#### StatisticalVariable Instance MCF

[PopulationDensity_Eurostat_NUTS3.mcf](./PopulationDensity_Eurostat_NUTS3.mcf)

#### Scripts

[PopulationDensity_preprocess_gen_tmcf.py](./PopulationDensity_preprocess_gen_tmcf.py)

## About the Import

### Processing Steps

`PopulationDensity_Eurostat_NUTS3.mcf` was handwritten.

To generate `PopulationDensity_Eurostat_NUTS3.tmcf` and `PopulationDensity_Eurostat_NUTS3.csv`, run:


This script offers three modes of operation: download, process, or both download and process.

```bash
1. Download and Process (python3 PopulationDensity_preprocess_gen_tmcf.py or no mode flag):
2. Download Only (python3 PopulationDensity_preprocess_gen_tmcf.py --mode=download):
3. Process Only (python3 PopulationDensity_preprocess_gen_tmcf.py --mode=process):
```

### Testing Procedure

How to Create Sample Data: Extract a subset of rows from your source input file to generate sample input and output CSV files.

To test import procedure, run the following command:

```
python3 PopulationDensity_preprocess_gen_tmcf_test.py

```

### Post-Processing Validation

- Wrote and ran
  [csv_template_mcf_compatibility_checker.py](./csv_template_mcf_compatibility_checker.py)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.
