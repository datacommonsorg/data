# Importing COVID19 Data for Johannesburg Into Data Commons

Author: Data Science for Social Impact

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset


### Download URL

CSV file is available for download from https://github.com/dsfsi/covid19za/blob/master/data/district_data/gp_johannesburg.csv.
The dataset is called `gp_johannesburg.csv`.

### Overview

This dataset is part of a larger dataset (Coronavirus COVID-19 (2019-nCoV) Data Repository for South Africa), which is created, maintained and hosted by Data Science for Social Impact research group. This dataset is a subset containing COVID-19 data for the City of Johannesburg.

The dataset details cumulative counts for cases, recoveries and deaths for Johannesburg and Johannesburg districts.


## About the Import

### Artifacts

#### Raw Data
- [gp_johannesburg.csv](gp_johannesburg.csv)

#### Cleaned Data
- [cleaned_data.csv](output/cleaned_data.csv)

#### Template MCFs
- [COVID19_JHB.tmcf](output/COVID19_JHB.tmcf)

#### Scripts
- [preprocess.py](preprocess.py)
- [preprocess_test.py](preprocess_test.py)

#### Test Data
- [test_data.csv](test_data/test_data.csv)
- [test_expected_data.csv](test_data/test_expected_data.csv)

#### Generating Artifacts:

`COVID19_JHB.tmcf` was generated using dc-import wizard and then ammended manually.

To generate `cleaned_data.csv`, run:

```bash
python3 preproccess.py
```

#### Post-Processing Validation

- Ran [dc-import tool](https://github.com/datacommonsorg/import/blob/master/docs/usage.md)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.

  - [report.json](validation/report.json)
  - [summary_report.html](validation/summary_report.html)

  There are no errors, only warnings for missing values.
