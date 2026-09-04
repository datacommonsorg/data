# Importing ChEMBL proteome data

## Table of Contents

- [Importing ChEMBL proteome data](#importing-chembl-proteome-data)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Schema Overview](#schema-overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
  - [Examples](#examples)

## About the Dataset

### Download URL

The ChEMBL database hosts a variety of datasets including, compound records, compounds, activities, assays, and targets. The ChEMBL data can be downloaded from the official [webpage](https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_29/). The data is in .txt and .fasta formats and had to be parsed into a csv version (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Overview

This directory stores the scripts used to convert the datasets obtained from ChEMBL into modified versions, for effective ingestion of data into the Data Commons knowledge graph.

The database links the ChEMBL ID, Uniprot ID, name, and sequence data of about various chemical compounds.

### Schema Overview

The schema representing chemical compound data from HMDB is defined in pre-defined. The tmcfs for each of the corresponding csv files can be found [here](https://github.com/suhana13/data/tree/add_hmdb_metabolites/scripts/biomedical/chembl/tmcf).

### Notes and Caveats

3 of the parsed files were in .fasta format. So, they had to be converted to a .csv format. However, the remaining two files were in .txt format and were easier to parse.

### License

This data is freely available to all users. However, the commercial usage of the database requires explicit permission of the authors. More information on the ChEMBL license can be found [here](https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_29/).

## About the import

- ### Artifacts

- #### Scripts

[`format_chembl_uniprot.py`](format_chembl_uniprot.py)
[`format_chembl29_fasta.py`](format_chembl29_fasta.py)
[`format_chembl29.py`](format_chembl29.py)
[`format_chemblBio_fasta.py`](format_chemblBio_fasta.py)
[`format_chemblBlast_fasta.py`](`format_chemblBlast_fasta.py`)

## Examples

This is a step-by-step workflow showing all the bash commands to run each of the python scripts and get the desired csv output.

- `To generate the formatted ChEMBL-uniprot mapping file`

```
python format_chembl_uniprot.py chembl_uniprot_mapping.txt chembl_uniprot.csv
```

- `To generate the formatted ChEMBL-chemreps file`

```
python format_chembl29.py chembl_29_chemreps.txt chembl_29.csv
```

- `To generate the ChEMBL file from its corresponding fasta input file`

```
python format_chembl29_fasta.py chembl_29.fa chembl_29_fasta.csv
```

- `To generate the ChEMBL-bio file from its corresponding fasta input file`

```
python format_chemblBio_fasta.py chembl_29_bio.fa chembl_bio_fasta.csv
```

- `To generate the ChEMBL-blast file from its corresponding fasta input file`

```
python format_chemblBlast_fasta.py chembl_29_blast.fa chembl_blast_fasta.csv
```
