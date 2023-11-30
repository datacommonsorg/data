# Importing the Diseases at Jensen Lab

## Table of Contents

- [Diseases at Jensen Lab](#importing-the-diseases-at-jensen-lab)
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

[The DISEASES at Jensen Lab](https://diseases.jensenlab.org/About) is a "weekly updated web resource that integrates evidence on disease-gene associations from automatic text mining, manually curated literature, cancer mutation data, and genome-wide association studies." The data has evidence with confidence scores that facilitate comparison of the different types and sources of evidence.

### Download Data

The Diseases database can be downloaded from their official website found [here](https://diseases.jensenlab.org/Downloads). We downloaded and cleaned the full versions of the following files:

- Text mining channel
- Knowledge channel
- Experiments channel

### Overview

"The files contain all links in the DISEASES database. All files start with the following four columns: gene identifier, gene name, disease identifier, and disease name. The knowledge files further contain the source database, the evidence type, and the confidence score. The experiments files instead contain the source database, the source score, and the confidence score. Finally, the textmining files contain the z-score, the confidence score, and a URL to a viewer of the underlying abstracts."

### Notes and Caveats

All the disease-gene associations have ICD-10 codes for the diseases. Some of the ICD-10 codes are ill-formatted, for ex: `ICD10:J9` or `ICD10:root`. Hence, the disease-gene associations with these values are excluded from the main import and are included in the log file which is present in this repository.

### License

This dataset is under a Creative Commons CC BY license.

## About the import

### Artifacts

#### Scripts

##### Bash Script

[`run.sh`](run.sh) downloads the experimental, manually curated, and text mining data from DISEASES at Jensen Lab and converts it into csv files formatted for import into the Data Commons knowledge graph.

##### Python Script

[`format_disease_jensen_lab.py`](format_disease_jensen_lab.py) parses the raw .tsv files with DISEASES at Jensen Lab into well formatted csv files with generated dcids.

#### Files

##### tMCF File

[`codingGenes-manual.tmcf`](tmcfs/codingGenes-manual.tmcf) contains the tmcf mapping to the csv of coding genes curated manually.

[`nonCodingGenes-manual.tmcf`](tmcfs/nonCodingGenes-manual.tmcf) contains the tmcf mapping to the csv of non-coding genes curated manually.

[`codingGenes-textMining.tmcf`](tmcfs/codingGenes-textMining.tmcf) contains the tmcf mapping to the csv of coding genes using textmining.

[`nonCodingGenes-textMining.tmcf`](tmcfs/nonCodingGenes-textMining.tmcf) contains the tmcf mapping to the csv of non-coding genes using textmining.

[`experiment.tmcf`](tmcfs/experiment.tmcf) contains the tmcf mapping to the csv of coding genes curated experimentally.

### Example

The following bash script can be run and it will take care of everything starting from data download to generating clean .csv files.

```
bash run.sh
```
