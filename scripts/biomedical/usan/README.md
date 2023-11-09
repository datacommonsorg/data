# Importing the United States Adopted Names (USAN) data

## Table of Contents

- [Importing the United States Adopted Names (USAN) data](#importing-the-united-states-adopted-names-usan-data)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download Data](#download-data)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [Files](#files)
  - [Example](#example)

## About the Dataset
The [United States Adopted Names (USAN) Council](https://www.ama-assn.org/about/united-states-adopted-names/usan-council) is co-sponsored by the American Medical Association, the United States Pharmacopeial Convention, Inc., and the American Pharmaceutical Association. The USAN Council’s goal is to provide meaningful designations for compounds, enhancing prescribing and patient safety. It was organized in 1964 to represent the health professions in the selection of appropriate nonproprietary names for drugs.

[USAN stems](https://www.ama-assn.org/about/united-states-adopted-names/united-states-adopted-names-approved-stems) represent common stems for which chemical and/or pharmacologic parameters have been established. These council-approved stems and their definitions are recommended for use in coining new nonproprietary drug names belonging to an established series of related agents. This provides meaningful designations for compounds that enhance prescription and patient safety. USAN appropriately incorporates this established class stem system. By doing so, similar compounds maintain a common "family" name that provides immediate recognition. 

### Download Data

The USAN stem data can be downloaded from their website [here](https://www.ama-assn.org/about/united-states-adopted-names/united-states-adopted-names-approved-stems). The data is in `.xlsx` format and had to be parsed first converted into a `.csv` format  (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting) for further data preprocessing. For the convenience of users, we have provided a raw .csv version of the data in this repository because viewing the raw .xlsx version is unsupported in many systems.

### Overview

This directory stores the script used to clean and convert the United States Adopted Names data into a `.csv` format, which is ready for ingestion into the Data Commons knowledge graph alongside a `.tmcf` file that maps the `.csv` to the defined schema. In this import the data is ingested as [USAdoptedNameStem](https://datacommons.org/browser/USAdoptedNameStem) entities into the graph.

The USAN Stem ID is mapped to other properties, namely, its name, definition, examples, stem type, word stem, specialization and year of creation.

### Notes and Caveats

The original format of the data was `.xlsx` and it was converted to a `.csv` file prior to ingestion into Data Commons. One of the key issues encountered during the import was working with a `.xlsx` file as it failed to be read by python due to different formatting. Hence, in order to preprocess the `.xlsx` file data, we first converted the file to a `.csv` format which was then read as a pandas dataframe in python. </br>

Another key issue with the data was that the substems and stems were not clearly listed as a dataframe, rather they had to mined using some complicated logic based on stem definitions and specializations.

Lastly, the data doesn't have the USAN stem years which is them fetched from chembl and merged into the existing USAN dataframe. 

### License

These data are nonproprietary, which by definition is in the public domain.

## About the import

### Artifacts

#### Scripts

##### Python Script

[`format_usan.py`](format_usan.py) parses the .csv file and converts it into a .csv with USAN stems mapped to their corresponding word stems.

#### Files

##### Data File

[`stem-list.csv`](stem-list.csv) contains USAN stem raw data
[`drug-mechanisms.tsv`](drug-mechanisms.csv) contains drug mechanisms data from chembl

##### tMCF File

[`usan.tmcf`](usan.tmcf) contains the tmcf mapping to the csv file, to generate an accurate tmcf-csv pair.

### Example

```
python3 format_usan.py stem-list.csv drug-mechanisms.tsv usan_output.csv
```
