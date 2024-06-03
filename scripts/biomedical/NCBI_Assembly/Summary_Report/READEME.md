# Importing NCBI Assembly Summary Report

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

1. [assembly_summary_genbank.txt](https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt).
2. [assembly_summary_refseq.txt](https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt).

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

- Working further on the script to make it more faster.

##### Bash Scripts

- [download.sh](scripts/download.sh) downloads the most recent release of the NCBI Assembly Summary Report data.
- [run.sh](scripts/run.sh) creates ncbi_assembly_summary.csv.
- [tests.sh](scripts/tests.sh) runs standard tests to check for proper formatting.

##### Python Scripts

- [process.py](scripts/process.py) creates the NCBI Assembly Summary Report formatted CSV files.
- [process_test.py](scripts/process_test.py) unittest script to test standard test cases on NCBI Assembly Summary Report.

#### tMCFs

- [ncbi_assembly_summary_report.tmcf](tMCF/ncbi_assembly_summary_report.tmcf) contains the tmcf mapping to the csv of NCBI Assembly Summary Report.



### Import Procedure

Download the most recent versions of NCBI Assembly Summary Report data:

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