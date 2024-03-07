# Importing Medical Subject Headings (MeSH) data from NCBI

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
    - [Run Tests](#run-tests)
    - [Import](#import)

## About the Dataset

“The Medical Subject Headings (MeSH) thesaurus is a controlled and hierarchically-organized vocabulary produced by the National Library of Medicine. It is used for indexing, cataloging, and searching of biomedical and health-related information”. Data Commons includes the Concept, Descriptor, Qualifier, Supplementary Record and Term elements of MeSH as described [here](https://www.nlm.nih.gov/mesh/xml_data_elements.html). More information about the dataset can be found on the official National Center for Biotechnology (NCBI) [website](https://www.ncbi.nlm.nih.gov/mesh/).
Pubchem is one of the largest reservoirs of chemical compound information. It is mapped to many other medical ontologies, including
MeSH. More information about compound IDs and other properties can be found on their official [website](https://pubchemdocs.ncbi.nlm.nih.gov/compounds).

### Download Data

All the terminology referenced in the MeSH data can be downloaded in various formats [here](https://www.nlm.nih.gov/databases/download/mesh.html). The current xml files version can also be downloaded by running [`download.sh`](download.sh). For the purpose of mapping all mesh terms with each other, two xml files are used, namely: `desc2022.xml` and `supp2022.xml`.
The csv version of the file containing PubChem Compound ID and names can also be downloaded by running[`download.sh`](download.sh)

### Overview

This directory stores the scripts used to convert the xml obtained from the NCBI webpage into five different csv files, each describing the relation between supplementary records, concepts, terms, qualifiers and descriptors, and generating dcids for each.
The MeSH data stores the vocabulary thesaurus used for indexing articles for PubMed. In addition, the scripts are used to map ther PubChem compound IDs to the MeSH descriptor and supplementary record IDs, joining on MeSH supplementary record name/PubChem compoundID.

- For mapping the MeSH descriptor ID with the MeSH supplementary record ID, the [supplementary file](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/supp2022.xml) is used.
- For mapping the MeSH descriptor ID with each of the three other IDs: concept ID, term ID, qualifier ID, the [descriptor file](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2022.xml) is used.
- For mapping the PubChem compound ID with the MeSH supplementary record and descriptor ID, the [pubchem file](https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-MeSH) is used.

### Notes and Caveats

The main main file and the mesh supplementary file are both XML formatted. In addition, they're about 300-600 GB worth of storage. This is one the major contributors of extended run time for the scripts. Extracting the information from XML formatted tags and converting it into well-formatted csv involve a lot of computationally heavy steps, which depends on the RAM of the user's system.

In order to run the script [`format_mesh.py`](format_mesh.py), the user requires the `mesh.xml` file, which spits out four different
csv files, each relating to descriptor, concept, qualifier and term.
In order to run the script [`format_mesh_record.py`](format_mesh_record.py), the user requires the `mesh_record.xml` file and the
`mesh-pubchem.csv` file which maps the record to descriptor and to the pubchem compound ID, and spits out two csv files. Here, the goal is to map the mesh terms to the pubchem database of compounds. This is accomplished by mapping the mesh record name to the pubchem compound name. In addition, each mesh entity has a descriptor ID which is in turn linked to mesh suplementary record ID, and thus ultimately linked to pubchem compound ID. 

### License

Any works found on National Library of Medicine (NLM) Web sites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

## About the import

### Artifacts

#### Scripts

[`format_mesh.py`](format_mesh.py) converts the original xml into four formatted csv files, which each can be imported alongside it's matching tMCF.
[`format_mesh_record.py`](format_mesh_record.py) converts the supplementary MeSH supplementary record file into a csv mapped to MeSH descriptor ID,
and it maps the MeSH supplementary records to pubchem compound IDs resulting in a second separate csv.
[`download.sh`](download.sh) downloads all the files from the NCBI webpage and stores them in the scratch directory.
[`mesh_run.sh`](mesh_run.sh) runs all the python commands generating six csv files in total.

#### tMCFs

The tMCF files that map each column in the corresponding CSV file to the appropriate property can be found [here](tmcf). They include:

- [`mesh_concept.tmcf`](tmcf/mesh_concept.tmcf)
- [`mesh_descriptor.tmcf`](tmcf/mesh_descriptor.tmcf)
- [`mesh_qualifier.tmcf`](tmcf/mesh_qualifier.tmcf)
- [`mesh_term.tmcf`](tmcf/mesh_term.tmcf)
- [`mesh_pubchem.tmcf`](tmcf/mesh_pubchem.tmcf)
- [`mesh_record.tmcf`](tmcf/mesh_record.tmcf)

### Schema

Each of the five csv + tMCF pair generated is an import of the MeSH ontology mapping to one of the four following entities: [MeSHConcept](https://datacommons.org/browser/MeSHConcept), [MeSHDescriptor](https://datacommons.org/browser/MeSHDescriptor), [MeSHQualifier](https://datacommons.org/browser/MeSHQualifier), [MeshSupplementaryRecord](https://datacommons.org/browser/MeSHSupplementaryRecord), and [MeSHTerm](https://datacommons.org/browser/MeSHTerm).


## Examples

### Run Tests

To run the unit tests for all the generated csv files:

1. Download the `unit-tests/` directory

2. Run tests for [`format_mesh.py`](format_mesh.py)

```
python3 mesh_test.py
```

3. Run tests for [`format_mesh_record.py`](format_mesh_record.py)

```
python3 mesh_record_test.py
```

### Import

To generate the four formatted csv files from xml:

1. Download the data to `scratch/`

```
bash download.sh
```

2. Generate cleaned CSV files

```
bash mesh_run.sh
```
