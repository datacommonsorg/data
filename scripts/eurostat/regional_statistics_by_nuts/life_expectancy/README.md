# Importing Eurostat Life Expectancy By Age, Sex (demo_r_mlifexp) Into Data Commons

Author: qlj-lijuan

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

This dataset reports life expectancy by age, gender in countries, NUTS1 and NUTS2 regions in Europe.

### Download URL

[TSV] file is available for [download](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_mlifexp/?format=TSV&compressed=true).

### License

See parent README.

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

- [preprocess.py](preprocess.py)
- [generate_mcf.py](generate_mcf.py)
- [test_preprocess.py](test_preprocess.py)

## Generating Artifacts

To generate the cleaned csv `demo_r_mlifexp_cleaned.csv`, run

This script offers three modes of operation: download, process, or both download and process.

```bash
1. Download and Process (python3 preprocess.py or no mode flag):
2. Download Only (python3 preprocess.py --mode=download):
3. Process Only (python3 preprocess.py --mode=process):
```

To generate `demo_r_mlifexp.tmcf` and `demo_r_mlifexp_statvar.mcf`, run:

```bash
python3 generate_mcf.py
```
### Testing Procedure

How to Create Sample Data: Extract a subset of rows from your source input file to generate sample input and output CSV files.

To test import procedure, run the following command:

```
python3 preprocess_test.py

```