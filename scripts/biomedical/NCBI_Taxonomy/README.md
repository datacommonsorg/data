# Importing NCBI Taxonomy Data

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

NCBI Taxonomy data can be downloaded from the National Center for Biotechnology Information (NCBI) Assembly database using their FTP Site
1. [ncbi_taxdump](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.Z). 
2. [ncbi_taxcat](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxcat.tar.gz).

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

- [download.sh](scripts/download.sh) downloads the most recent release of the NCBI Taxonomy data.
- [run.sh](scripts/run.sh) creates new taxonomy enum mfc and converts data into formatted CSV for import of data using categories.dmp, division.dmp, host.dmp, names.dmp & nodes.dmp files from download location
- [tests.sh](scripts/tests.sh) runs standard tests to check for proper formatting of taxonomy enum mfc file.

##### Python Scripts

- [format_ncbi_taxonomy.py](scripts/format_ncbi_taxonomy.py) creates the taxonomy enum mcf and formatted CSV files.
- [format_ncbi_taxonomy_test.py](scripts/format_ncbi_taxonomy.py) unittest script to test standard test cases on taxonomy enum mcf.

#### tMCFs

- [ncbi_taxonomy_schema.mcf](tMCFs/ncbi_taxonomy.tmcf) contains the tmcf mapping to the csv of taxonomy.

#### Schema MCF

- [ncbi_taxonomy_schema.mcf](schema_mcf/ncbi_taxonomy_schema.mcf) contains the schema mcf.


### Import Procedure

Download the most recent versions of NCBI Taxonomy data:

```bash
sh download.sh
```

Generate the enum schema MCF & formatted CSV:

```bash
sh run.sh
```


### Test 

To run tests:

```bash
sh tests.sh
```