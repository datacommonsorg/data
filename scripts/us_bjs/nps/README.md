# Importing BJS National Prisoner Statistics Into Data Commons

Author: chejennifer

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Procedure](#import-procedure)

## About the Dataset

### Download URL

data is available for download from https://www.icpsr.umich.edu/web/NACJD/studies/37639.

### Overview
1. Jurisdiction by various factors and combinations of factors including: location, gender, race, correctional facility type, sentencing lengths
2. Custody by various factors and combinations of factors including: citizenship, correctional facility type, sentencing lengths
Admission and Discharge
3. Admission and Discharge

### Notes and Caveats
1. There is discontinuity in the years of collection and there are some fields in the data with missing values due to various reasons.
1. There are many pages of notes on the values of collections from different states. The information in these notes have not been included in the data. 
1. NPS collection items have several major changes over the years and there are items that were added, deleted, modified, or deleted and added back later.


#### Cleaned Data
- [national_prison_stats.csv](national_prison_stats.csv).

#### Template MCFs
- [national_prison_stats.tmcf](national_prison_stats.tmcf).

#### StatisticalVariable Instance MCF
- [nps_statvars.mcf](nps_statvars.mcf).

#### Scripts
- [import_data.py](import_data.py): BJS National Prison Statistics import script.


## Import Procedure

>To import BJS National Prison Statistics data:
1. download the data from https://www.icpsr.umich.edu/web/NACJD/studies/37639
2. run the following command with the option -i followed by the path to the tsv data file that was downloaded:
```
python3 import_data.py
```