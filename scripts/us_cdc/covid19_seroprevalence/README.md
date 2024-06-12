# Importing CDC COVID-19 Seroprevalence Data

Author: Padma Gundapaneni @padma-g

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [License](#license)
    5. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)

## About the Dataset

### Download URL
The dataset can be downloaded at the following link from [the CDC website](https://data.cdc.gov/Laboratory-Surveillance/Nationwide-Commercial-Laboratory-Seroprevalence-Su/d2tw-32xv).

The downloaded data is in .csv format.

### Overview
The data imported in this effort is from the CDC's [Nationwide Commerical Laboratory Seroprevalence Survey](https://www.cdc.gov/coronavirus/2019-ncov/cases-updates/commercial-lab-surveys.html), and is provided by
the [National Center for Immunization and Respiratory Diseases (NCIRD), Division of Viral Diseases](https://www.cdc.gov/ncird/index.html). The dataset provides prevalence estimates of "the percentage of people who were previously infected with SARS-CoV-2, the virus that causes COVID-19 disease" for February 2020 to June 2021.

### Notes and Caveats

None.

### License
The data is made available for public-use by the [CDC](https://www.cdc.gov/coronavirus/2019-ncov/cases-updates/index.html). Users of CDC website must comply with the CDC's [data use policies](https://www.cdc.gov/other/agencymaterials.html).

### Dataset Documentation and Relevant Links
These data were collected and provided by the [National Center for Immunization and Respiratory Diseases (NCIRD), Division of Viral Diseases](https://www.cdc.gov/ncird/index.html). The documentation for the datasets is accessible [here](https://www.cdc.gov/coronavirus/2019-ncov/cases-updates/commercial-lab-surveys.html).

## About the Import

### Artifacts

#### Scripts
[`parse_data.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/covid19_seroprevalence/parse_data.py)

#### Test Scripts
[`parse_data_test.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/covid19_seroprevalence/parse_data_test.py)

#### tMCFs
[`count_data.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/covid19_seroprevalence/count_data.tmcf)

[`percent_data.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/covid19_seroprevalence/percent_data.tmcf)

### Import Procedure

#### Testing

##### Test Data Cleaning Script

To test the data cleaning script, run `parse_data_test.py`:

```bash
$ python3 parse_data_test.py
```

The expected output of this test can be found in the [`test_data`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/covid19_seroprevalence/test_data/) directory.

#### Data Processing Steps

`@input_file_name` - path to the input csv file to be cleaned

`@output_file_count` - path to write the cleaned count data csv file

`@output_file_percent` - path to write the cleaned percent data csv file

To clean the data, run `parse_data.py`:

```bash
$ python3 parse_data.py input_file_name output_file_count output_file_percent
```
