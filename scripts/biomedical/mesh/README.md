# Importing Medical Subject Headings (MeSH) data from NCBI

## Table of Contents

- [Importing Medical Subject Headings (MeSH) data from NCBI](#importing-medical-subject-headings-mesh-data-from-ncbi)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
  - [Examples](#examples)

## About the Dataset

Medical Subject Headings (MeSH) is a hierarchically-organized terminology for indexing and cataloging of biomedical information. More information about the dataset can be found on the official NCBI [website](https://www.ncbi.nlm.nih.gov/mesh/).

### Download URL

All the terminology referenced in the MeSH data can be downloaded in various formats, [here](https://www.ncbi.nlm.nih.gov/mesh/).

### Overview

This directory stores the script used to convert the xml obtained from the NCBI webpage into 4 different csv files, each describing the relation between concepts, terms, qualifiers and descriptors, and generating dcids for each.

The MeSH data stores the vocabulary thesaurus used for indexing articles for PubMed.

### Notes and Caveats

The data is formatted in XML format. So, it had to be parsed into CSV format, which might have contributed to the extended runtime of the program, depending on the RAM of the user's system.

- ### License

Any works found on National Library of Medicine (NLM) Web sites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

## About the import

### Artifacts

#### Scripts

[`format_mesh.py`](format_mesh.py)

## Examples

To generate the 4 formatted csv files from xml:

```
python format_mesh.py desc2021.xml
```
