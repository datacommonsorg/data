# Importing CDC 500 PLACES Data

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
The datasets can be downloaded at the following links from [the CDC website](https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places&sortBy=newest&utf8).
- [PLACES: Local Data for Better Health, Census Tract Data](https://chronicdata.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-Census-Tract-D/cwsq-ngmh)
- [PLACES: Local Data for Better Health, County/Country Data](https://chronicdata.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-County-Data-20/swc5-untb)
- [PLACES: Local Data for Better Health, Place (City) Data](https://chronicdata.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-Place-Data-202/eav7-hnsx)
- [PLACES: Local Data for Better Health, ZCTA (Zip Code) Data](https://chronicdata.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-ZCTA-Data-2020/qnzd-25i4)

All the downloaded data is in .csv format. 

### Overview
The data imported in this effort is from the CDC's [500 Places project](https://www.cdc.gov/places/about/index.html), a continuation of the [500 Cities project](https://www.cdc.gov/places/about/500-cities-2016-2019/index.html), and is provided by the CDC's [National Center for Chronic Disease Prevention and Health Promotion](https://www.cdc.gov/chronicdisease/index.htm). The datasets contain "estimates for 27 measures: 5 chronic disease-related unhealthy behaviors, 13 health outcomes, and 9 on use of preventive services. These estimates can be used to identify emerging health problems and to inform development and implementation of effective, targeted public health prevention activities."

### Notes and Caveats

None.

### License
The data is made available for public-use by the [CDC](https://www.cdc.gov/nchs/data_access/ftp_data.htm). Users of CDC National Center for Health Statistics Data must comply with the CDC's [data use agreement](https://www.cdc.gov/nchs/data_access/restrictions.htm).

### Dataset Documentation and Relevant Links
These data were collected and provided by the [CDC National Center for Chronic Disease Prevention and Health Promotion](https://www.cdc.gov/chronicdisease/index.htm). The documentation for the datasets is accessible [here](https://www.cdc.gov/places/about/index.html).

## About the Import

### Artifacts

#### Scripts
[`parse_cdc_places.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/500_places/parse_cdc_places.py)

#### Test Scripts
[`parse_cdc_places_test.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/500_places/parse_cdc_places_test.py)

#### tMCFs
[`cdc_places.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/500_places/cdc_places.tmcf)

### Import Procedure

#### Testing

##### Test Data Cleaning Script

To test the data cleaning script, run:

```bash
$ python3 parse_cdc_places_test.py
```

The expected output of this test can be found in the [`test_data`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/500_places/test_data/) directory.

#### Processing Steps

`@input_file_name` - path to the input csv file to be cleaned

`@output_file_name` - path to write the cleaned csv file

`@delimiter` - delimiter for the input csv file

To clean the data files, run:

```bash
$ python3 parse_cdc_places.py input_file_name output_file_name delimiter
```
