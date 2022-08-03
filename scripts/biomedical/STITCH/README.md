# Importing dbSNP data from NCBI

## Table of Contents

- [Importing Medical Subject Headings (MeSH) data from NCBI](#importing-medical-subject-headings-mesh-data-from-ncbi)
  - [About the Dataset](#about-the-dataset)
    - [Download Data](#download-data)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [Files](#files)
     - [Schema Artifacts](#schema)
       - [Scripts](#scripts)
       - [Output Schema MCF Files](#output-schema-mcf-files)
  - [Examples](#examples)
    - [Run Tests](#run-testers)
    - [Import](#import)

# About the Dataset
[STITCH](http://stitch.embl.de/cgi/input.pl?UserId=f68rPwGhmUhl&sessionId=URI01tKFfMAQ) ('Search Tool for Interacting Chemicals') is a public-domain database of 430,000 chemicals. It contains "known and predicted interactions between chemicals and proteins. The interactions include direct (physical) and indirect (functional) associations; they stem from computational prediction, from knowledge transfer between organisms, and from interactions aggregated from other (primary) databases." The last time the database was updated was in 2016. 

### Download Data
Data was downloaded as TSVs from the [STITCH website](http://stitch.embl.de/cgi/download.pl). Files for [sources.tsv](http://stitch.embl.de/download/chemical.sources.v5.0.tsv.gz) and [inchikeys.tsv](http://stitch.embl.de/download/chemicals.inchikeys.v5.0.tsv.gz) and [chemicals.tsv](http://stitch.embl.de/download/chemicals.v5.0.tsv.gz) were downloaded, cleaned, and ingested. The current versions of the TSV files can also be downloaded and processed by running [`download.sh`](download.sh).

### Overview

This directory stores the scripts used to download, clean, and convert the STITCH datasets into one CSV file. 

### Notes and Caveats

All three datasets have stereo compound IDs (CID) and flat CIDs, which is what we used to merge them. 

chemical.sources.v5.0.tsv
This file contained different source codes for various chemicals including: ChEMBL, ChEBI, ATC, BindingDB, KEGG, PS (PubChem Substance IDs of similar compounds), and PC (PubChem Compound IDs of similar compounds). We removed the PC values that were an exact match to the CID of the particular chemical on a given row.

chemicals.inchikeys.v5.0.tsv 
There were some mismatched compound stereo IDs and compound flat IDs included in the inchikeys.tsv file, so these rows from the dataset were excluded. 
We created a same_as column in the final CSV of the Chemical Compound DCIDs in which the InChIkey in the dataset matches the InChIkey in Data Commons. The value in that column is left blank if the InChIkey in that corresponding row does not match any InChIkey found in Data Commons.

chemicals.v5.0.tsv.gz
This file contained chemical name, molecular weight, and SMILES string. Some of the longer chemical names are truncated. 

After merging the datasets, we added two columns for the corresponding MeSHDescriptor DCIDs and ChEMBL DCIDs through querying the Biomedical Data Commons. We also added a new DCID that is based on the PubChem Compound ID formatted as 'chem/CID#'. The text columns have been formatted to have double quotes.  

This import has large data storage and compute requirements to execute. This includes 25 GB for storing the original files.


### License

All data downloaded for this import belongs to STITCH. Any works found on the STITCH website may be licensed — both for commercial and for academic institutions. More information about the license can be found [here](http://stitch.embl.de/cgi/access.pl?UserId=f68rPwGhmUhl&sessionId=URI01tKFfMAQ&footer_active_subpage=licensing).

# About the Import

## Artifacts

### Scripts

#### Shell Scripts
[`download.sh`](download.sh) downloads the three STITCH datasets and prepares it for data cleaning and processing.

#### Python Scripts
[`compile_stitch.py`](compile_stitch.py) cleans and merges the three STITCH datasets into one CSV.

#### Test Scripts
[`test_compile_stitch.py`](test_compile_stitch.py) tests the compile_stitch.py script.


### Files

#### Test Files
[`test_file1.tsv`](test_file1.tsv) subsetted the sources.tsv file to only include PubChem Compound IDs 1-20
[`test_file2.tsv`](test_file2.tsv) subsetted the inchikeys.tsv file to only include PubChem Compound CIDs 1-20
[`test_file3.tsv`](test_file3.tsv) subsetted the chemicals.tsv file to only include PubChem Compound CIDs 1-20


## Examples

### Run Tests

1. To test [`compile_stitch.py`](compile_stitch.py) run:

```
python test_compile_stitch.py
```

### Import

1. Download the data to `scratch/`.

```
bash download.sh
```

2. Run the script to clean and merge the three datasets into an output CSV, which is needed for import into the graph. 

```
python compile_stitch.py 
  scratch/sources_sorted.tsv 
  scratch/inchikeys_sorted.tsv
  scratch/chemicals_no_header.tsv
```