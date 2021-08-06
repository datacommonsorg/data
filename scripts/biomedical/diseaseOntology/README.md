# Importing the Disease Ontology (DO) data

## Table of Contents

- [Importing the Disease Ontology (DO) data](#importing-the-disease-ontology-do-data)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Schema Overview](#schema-overview)
    - [Notes and Caveats](#notes-and-caveats)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
  - [Examples](#examples)

## About the Dataset

### Download URL

The human disease ontology data can be downloaded from their official github repository [here](https://www.vmh.life/#human/all). The data is in `.owl` format and had to be parsed into a `.csv` format (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Overview

The Disease Ontology database provides a standardized ontology for human diseases, for the purposes of consistency and reusability. It contains extensive cross mapping of DO terms to other databases, namely, MeSH, ICD, NCI’s thesaurus, SNOMED and OMIM. More information on the database can be found [here](https://disease-ontology.org).

This directory stores the script used to convert the dataset obtained from DO into a modified version, for effective ingestion of data into the Data Commons knowledge graph.

### Schema Overview

The schema representing reaction, metabolite and microbiome data from VMH is defined in [DO.mcf](https://raw.githubusercontent.com/suhana13/ISB-project/main/combined_list.mcf) and [DO.mcf](https://raw.githubusercontent.com/suhana13/ISB-project/main/combined_list_enum.mcf).

This dataset contains several instances of the class `Disease` and it has multiple properties namely, "parent", "diseaseDescription", "alternativeDOIDs", "diseaseSynonym", "commonName", "icdoID", "meshID", "nciID", "snowmedctusID", "umlscuiID", "icd10CMID", "icd9CMID", "orDOID", "gardID", "omimID", "efoID", "keggDiseaseID", and "medDraID"

### Notes and Caveats

The original format of the data was `.owl` and it was converted to a `.csv` file prior to ingestion into Data Commons.

- ### License

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
