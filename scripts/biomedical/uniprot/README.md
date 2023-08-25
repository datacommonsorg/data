# Importing Universal Protein Resource (Uniprot) data

## Table of Contents

- [Importing Uniprot data](#importing-universal-protein-resource-uniprot-data)
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

The Universal Protein Resource (UniProt) is a comprehensive resource for protein sequence and annotation data. The UniProt data can be downloaded from the official [webpage](https://www.uniprot.org/help/downloads). The data is in a .fasta format and had to be parsed into a csv version (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Overview

This directory stores the scripts used to convert Swiss-Prot files into formatted csv files for effective ingestion of data into the Data Commons knowledge graph.

The database links the uniprot proteins to their corresponding protein-coding genes, the organism it belongs to, and the entire amino acid sequence.

### Schema Overviews

The schema representing [proteins](https://www.datacommons.org/browser/Protein) and [genes](https://www.datacommons.org/browser/Gene) is already present in the data commons knowledge graph. We're bringing in additional schema for the evidence supporting the existence of the protein.

### Notes and Caveats

The original file was .fasta format. So, it had to be converted to a .csv format which might've added to extra run time for the script to format it.

### License

This data is freely available to all users. It is available under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. More information on the UniProt license can be found [here](https://www.uniprot.org/help/license).

## About the import

- ### Artifacts

- #### Scripts

[`format_uniprot.py`](format_uniprot.py)

## Examples

This is a step-by-step workflow showing all the bash commands to run each of the python scripts and get the desired csv output.

- `To download the UniProt file`

```
curl https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot.fasta.gz --output uniprot.fasta.gz
```

- `To unzip the UniProt file`

```
gzip -d uniprot.fasta.gz
```

- `To run the script`

```
python3 format_uniprot.py uniprot.fasta formatted_uniprot.csv
```
