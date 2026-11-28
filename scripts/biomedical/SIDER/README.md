# Importing the Side Effect Resource (SIDER) database

## Table of Contents

- [Side Effect Resource (SIDER) database](#importing-the-side-effect-resource-sider-database)
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

[The Side Effect Resource (SIDER)](http://sideeffects.embl.de/) is a database that contains information on marketed medicines and their recorded adverse reactions.The information includes side effect frequency, drug and side effect classifications as well as links to further information, for example drug–target relations. However, due to license restrictions, we will be bringing in only ATC-PubChem mappings present in the database. 

### Download Data

The data can be downloaded from the official website which can be found [here](http://sideeffects.embl.de/download/).

### Overview

This directory stores the script used to clean and convert the SIDER data into a `.csv` format, which is ready for ingestion into the Data Commons knowledge graph alongside a `.tmcf` file that maps the `.csv` to the defined schema. Due to licensing issues mentioned in [Notes and Caveats](#notes-and-caveats), only a small subset of SIDER database could be ingested in the datacommons knowledge graph. 

### Notes and Caveats

As discussed above, since most of the data is extracted from side effects from drug labels which is under a Creative Commons Attribution-Noncommercial-Share Alike 4.0 License, it can't be brought in with the datacommons knowledge graph. However, the mappings between PubChem Compound IDs and ATC codes are under a Creative Commons Commercial license and thus, can be brought in to the knowledge graph.

### License

## About the import

### Artifacts

#### Scripts

##### Python Script

[`format_atc_pubchem.py`](format_atc_pubchem.py) parses the raw .csv file and converts it into a .csv with ATC codes mapped to their corresponding properties.

#### Files

##### tMCF File

[`drugs_atc.tmcf`](drugs_atc.tmcf) contains the tmcf mapping to the csv file, to generate an accurate tmcf-csv pair.

### Example

```
python3 format_atc_pubchem.py
```
