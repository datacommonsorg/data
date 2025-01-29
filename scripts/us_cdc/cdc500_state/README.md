# Importing CDC 500 STATES Data

Author: Padma Gundapaneni @padma-g

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Overview](#overview)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)

## About the Dataset

### Overview
The state level data is aggragated from city level data coming from CDC500 import. 

To get the data for this import run:
```bash
$ python3 process.py
```

## About the Import

### Artifacts

#### Scripts
[`process.py`](https://github.com/datacommonsorg/data/blob/master//scripts/us_cdc/cdc500_state/process.py)


#### tMCFs
[`cdc500_state.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/cdc500_state/cdc500_state.tmcf)

### Import Procedure

#### Data Download and Processing Steps

To get the data for this import run:

```bash
$ python3 process.py
```
