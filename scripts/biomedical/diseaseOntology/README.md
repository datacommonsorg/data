# Importing the Disease Ontology (DO) data

## Table of Contents

- [Importing the Disease Ontology (DO) data](#importing-the-disease-ontology-do-data)
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
  - [Examples](#examples)
    -[Run Tests](#run-tests)
    -[Import](#import)

## About the Dataset
[Disease Ontology](https://disease-ontology.org) (DO) is a standardized ontology for human disease that was developed "with the purpose of providing the biomedical community with consistent, reusable and sustainable descriptions of human disease terms, phenotype characteristics and related medical vocabulary disease concepts through collaborative efforts of biomedical researchers, coordinated by the University of Maryland School of Medicine, Institute for Genome Sciences.

The Disease Ontology semantically integrates disease and medical vocabularies through extensive cross mapping of DO terms to MeSH, ICD, NCI’s thesaurus, SNOMED and OMIM."

### Download Data

The human disease ontology data can be downloaded from their official github repository [here](https://www.vmh.life/#human/all). The data is in `.owl` format and had to be parsed into a `.csv` format (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Overview

This directory stores the script used to download, clean, and convert the Disease Ontology data into a `.csv` format, which is ready for ingestion into the Data Commons knowledge graph alongside a `.tmcf` file that maps the `.csv` to the defined schema. In this import the data is ingested as [Disease](https://datacommons.org/browser/Disease) entities into the graph.

### Notes and Caveats

The original format of the data was `.owl` and it was converted to a `.csv` file prior to ingestion into Data Commons.

### License

This data is under a Creative Commons Public Domain Dedication [CC0 1.0 Universal license](https://disease-ontology.org/resources/do-resources).

## About the import

### Artifacts

#### Scripts

`format_disease_ontology.py`

## Examples

To generate the formatted csv file from owl:

```
python format_disease_ontology.py humanDO.owl humanDO.csv
```
