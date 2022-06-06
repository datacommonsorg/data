# Importing Medical Subject Headings (MeSH) data from NCBI

## Table of Contents

- [Importing Medical Subject Headings (MeSH) data from NCBI](#importing-medical-subject-headings-mesh-data-from-ncbi)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [tMCFs](#tmcfs)
     - [Schema](#schema)
  - [Examples](#examples)

## About the Dataset

“The Medical Subject Headings (MeSH) thesaurus is a controlled and hierarchically-organized vocabulary produced by the National Library of Medicine. It is used for indexing, cataloging, and searching of biomedical and health-related information”. Data Commons includes the Concept, Descriptor, Qualifier, and Term elements of MeSH as described [here](https://www.nlm.nih.gov/mesh/xml_data_elements.html). More information about the dataset can be found on the official National Center for Biotechnology (NCBI) [website](https://www.ncbi.nlm.nih.gov/mesh/).

### Download URL

All the terminology referenced in the MeSH data can be downloaded in various formats [here](https://www.nlm.nih.gov/databases/download/mesh.html). The current xml file version can also be downloaded by running [`download.sh`](download.sh)

### Overview

This directory stores the script used to convert the xml obtained from the NCBI webpage into four different csv files, each describing the relation between concepts, terms, qualifiers and descriptors, and generating dcids for each.

The MeSH data stores the vocabulary thesaurus used for indexing articles for PubMed.

### Notes and Caveats

The data is formatted in XML format. So, it had to be parsed into CSV format, which might have contributed to the extended runtime of the program, depending on the RAM of the user's system.

### License

Any works found on National Library of Medicine (NLM) Web sites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

## About the import

### Artifacts

#### Scripts

[`format_mesh.py`](format_mesh.py) converts the original xml into four formatted csv files, which each can be imported alongside it's matching tMCF. 

#### tMCFs

The tMCF files that map each column in the corresponding CSV file to the appropriate property can be found [here](tmcf). They include:
  * [`mesh_concept.tmcf`](tmcf/mesh_concept.tmcf)
  * [`mesh_descriptor.tmcf`](tmcf/mesh_descriptor.tmcf)
  * [`mesh_qualifier.tmcf`](tmcf/mesh_qualifier.tmcf)
  * [`mesh_term.tmcf`](tmcf/mesh_term.tmcf)

### Schema

Each csv + tMCF pair generated is an import of the MeSH ontology mapping to one of the four following entities: [MeSHConcept](https://datacommons.org/browser/MeSHConcept), [MeSHDescriptor](https://datacommons.org/browser/MeSHDescriptor), [MeSHQualifier](https://datacommons.org/browser/MeSHQualifier), or [MeSHTerm](https://datacommons.org/browser/MeSHTerm).

## Examples

To generate the four formatted csv files from xml:

1. Download the data to `scratch/`.

```
bash download.sh
```

2. Generate cleaned CSV.

```
python format_mesh.py scratch/mesh.xml
```
