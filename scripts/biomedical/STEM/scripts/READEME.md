# Importing USAN STEM

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Database Overview](#database-overview)
    3. [Schema Overview](#schema-overview)
    4. [Notes and Caveats](#notes-and-caveats)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)
    3. [Test](#test)


## About the Dataset

### Download URL

1. [usan.xlsx](https://www.ama-assn.org/system/files/stem-list-cumulative.xlsx). 

### Database Overview

Need to add notes

### Schema Overview

Need to add notes

### Notes and Caveats

Need to add notes

### License

Need to add notes

### Dataset Documentation and Relevant Links

Need to add notes

## About the import

### Artifacts

#### Scripts

##### Bash Scripts

- [download.sh](scripts/download.sh) downloads the most recent release of the USAN STEM data.
- [run.sh](scripts/run.sh) creates usan.csv with new nodes.
- [tests.sh](scripts/tests.sh) runs standard tests to check for proper formatting of usan stem.

##### Python Scripts

- [format_usan.py](scripts/format_usan.py) creates the usan stem formatted CSV files.
- [format_usan_test.py](scripts/format_usan_test.py) unittest script to test standard test cases on usan stem.

#### tMCFs

- [usan_tmcf.tmcf](tMCFs/usan_tmcf.tmcf) contains the tmcf mapping to the csv of STEM.



### Import Procedure

Download the most recent versions of USAN STEM data:

```bash
sh download.sh
```

Generate the formatted CSV:

```bash
sh run.sh
```


### Test 

To run tests:

```bash
sh tests.sh
```