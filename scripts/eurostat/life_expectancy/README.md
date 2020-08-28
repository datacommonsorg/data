
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

This dataset reports life expectancy by age, gender in countries, NUTS1 and NUTS2 regions in Europe.

## Import Artifacts

### Raw Data
- [demo_r_mlifexp.tsv](demo_r_mlifexp.tsv)

### Cleaned Data
- [demo_r_mlifexp_cleaned.csv](demo_r_mlifexp_cleaned.csv)

### Template MCFs
- [demo_r_mlifexp.tmcf](demo_r_mlifexp.tmcf)

### StatisticalVariable Instance MCF
- [demo_r_mlifexp_statvar.tmcf](demo_r_mlifexp_statvar.tmcf)

### Scripts
-  [preprocess.py](preprocess.py)
-  [generate_mcf.py](generate_mcf.py)
-  [test_preprocess.py](test_preprocess.py)

### Notes


## Generating Artifacts
To generate the cleaned csv `demo_r_mlifexp_cleaned.csv`, run

```bash
python3 preprocess.py
```

To generate `demo_r_mlifexp.tmcf` and `demo_r_mlifexp_statvar.mcf`, run:

```bash
python3 generate_mcf.py
```