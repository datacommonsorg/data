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

The human disease ontology data can be downloaded from their official github repository [here](https://github.com/DiseaseOntology/HumanDiseaseOntology/tree/main/src/ontology). The data is in `.owl` format and had to be parsed into a `.csv` format (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting). One can also download the data by simply running the bash script [`download.sh`](download.sh).

### Overview

This directory stores the script used to download, clean, and convert the Disease Ontology data into a `.csv` format, which is ready for ingestion into the Data Commons knowledge graph alongside a `.tmcf` file that maps the `.csv` to the defined schema. In this import the data is ingested as [Disease](https://datacommons.org/browser/Disease) entities into the graph.

The disease ontology ID is mapped to other ontologies, namely ICDO (International Classification of Diseases for Oncology), NCI (National Cancer Institute), SNOWMED ( Systematized Nomenclature of Medicine), UMLSCUI (Unified Medical Language System), ORDO (Orphanet Rare Disease Ontology), GARD (Genetic and Rare Diseases), OMIM (Online Mendelian Inheritance in Man),
EFO (Experimental Factor Ontology), MEDDRA (Medical Dictionary for Regulatory Activities) and MeSH (Medical Subject Headings).

In addition, the data stores the parent class and alternative IDs for the disease of interest.

### Notes and Caveats

The original format of the data was `.owl` and it was converted to a `.csv` file prior to ingestion into Data Commons. One of the key issues encountered during the import was that all other ontologies were grouped under the same tag. So, to divide each ontology into its separate group or column, the prefixes for each ID were used. In addition, the disease description tag was misformatted with various special characteristics that had to be programmatically removed.

### License

This data is under a Creative Commons Public Domain Dedication [CC0 1.0 Universal license](https://disease-ontology.org/resources/do-resources).

## About the import

### Artifacts

#### Scripts

##### Shell Script

[`download.sh`](download.sh) downloads the HumanDO owl file in the scratch directory

##### Python Script

[`format_disease_ontology.py`](format_disease_ontology.py) parses the .owl file and converts it into a .csv with disease ontology mappings to other ontologies.

##### Test Script

[`disease_ontology_test.py`](disease_ontology_test.py) tests the given script on some test data.

#### Files

##### Test File

[`test-do.xml`](test-do.xml) contains test data

[`test-output.csv`](test-output.csv) contains the expected output

##### tMCF File

[`disease_ontology.tmcf`](disease_ontology.tmcf) contains the tmcf mapping to the csv file, to generate an accurate tmcf-csv pair.

### Examples

#### Run Tests

To test disease_ontology_test.py run:

```
python disease_ontology_test.py unit-tests/test-do.owl unit-tests/test-output.owl
```

#### Import

1. Download data to scratch/.

```
bash download.sh
```

2. Clean and convert the downloaded Disease Ontology data into `.csv` format

```
python format_disease_ontology.py HumanDO.owl HumanDO.csv
```