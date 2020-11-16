# Census of India - Imports

This directory stores all scripts used to import datasets from the Census of India into Data Commons.

## Base Class - CensusPrimaryAbstractDataLoaderBase
`india_census.common.base.CensusPrimaryAbstractDataLoaderBase` is the base class for all census primary abstract data loaders. It has all the features required to clean and process the data. A specific census dataset loader can extend this class and can override any methods if required.

It has one public function `process()` which internally downloads the data, cleans the data, creates the MCF, TMCF, and cleaned CSV file.


## primary_abstract_data_variables.csv
A CSV file that defines census attributes. It's inside the package `india_census.common.base`. It has the following columns

- columnName
- description
- populationType
- statType
- measuredProperty- 
- gender
- age
- socialCategory 
- literacyStatus 
- workerStatus
- workerClassification
- workCategory
- workPeriod

This is used for creating the MCF files.

## Primary Census Abstract Total (India, States/UTs - District Level) Overview
- Refer the read me inside [primary_census_abstract_data](./primary_census_abstract_data/readme.md) folder.


## Primary Census Abstract - Scheduled Caste (India, States/UTs - District Level) Overview
- Refer the read me inside [primary_census_abstract_scheduled_caste](./primary_census_abstract_scheduled_caste/readme.md) folder.


## Primary Census Abstract - Scheduled Tribe (India, States/UTs - District Level) Overview
- Refer the read me inside [primary_census_abstract_scheduled_caste](./primary_census_abstract_scheduled_tribe/readme.md) folder.