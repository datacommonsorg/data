
# Importing Eurostat Life Expectancy By Age, Sex (demo_r_mlifexp)  Into Data Commons

Author: qlj-lijuan

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

tsv file is available for download from https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_mlifexp.tsv.gz.

### Overview

This dataset reports life expectancy by age, gender in countries and NUTS2 regions in Europe.
The dataset is broken into 2 parts: the country level and NUT2 regions for the convenience of importing into DataCommons

This dataset contains the following info:
- age: ranges from 1 to 85 years at the step of 1 year + below 1 year + beyond 85 years
- gender: Female, Male, Total
- geo: countries + NUTS2 regions
- life expectancy

### Notes and Caveats


### License


### Dataset Documentation and Relevant Links 



## Import Artifacts

### Raw Data
- [demo_r_mlifexp.tsv](demo_r_mlifexp.tsv)

### Cleaned Data
- [demo_r_mlifexp_cleaned.csv](demo_r_mlifexp_cleaned.csv)
- [demo_r_mlifexp_country_cleaned.csv](demo_r_mlifexp_country_cleaned.csv)

### Template MCFs
- [demo_r_mlifexp.tmcf](demo_r_mlifexp.tmcf)
- [demo_r_mlifexp_country.tmcf](demo_r_mlifexp_country.tmcf)

### StatisticalVariable Instance MCF
- [demo_r_mlifexp_statvar.tmcf](demo_r_mlifexp_statvar.tmcf)

### Scripts
-  [preprocess.py](preprocess.py)
-  [generate_mcf.py](generate_mcf.py)
-  [test_preprocess.py](test_preprocess.py)

### Notes


## Generating Artifacts
To generate the cleaned csv `demo_r_mlifexp_cleaned.csv` and `demo_r_mlifexp_country_cleaned.csv`, run

```bash
python3 preprocess.py
```

To generate `demo_r_mlifexp.tmcf`, `demo_r_mlifexp_country.tmcf` and `demo_r_mlifexp_statvar.mcf`, run:

```bash
python3 generate_mcf.py
```




