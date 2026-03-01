# Importing the Diseases at Jensen Lab

## Table of Contents
1. [About the Dataset](#about-the-dataset)
   1. [Download Data](#download-data)
   2. [Overview](#overview)
   3. [Notes and Caveats](#notes-and-caveats)
   4. [dcid Generation](#dcid-generation)
   5. [License](#license)
   6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the import](#about-the-import)
   1. [Artifacts](#artifacts)
      1. [Scripts](#scripts)
      2. [tMCF Files](#tmcf-files)
   3. [Import Procdeure](#import-procedure)
   4. [Tests](#tests) 

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

The disease for each association is indicated either by either a Disease Ontology ID (DOID) or an ICD10 code. For the associations of a gene with an ICD10 code, there is a heirarchical repetitive nature with how the ICD10 code is represented in the original data. For example in the experiment file there is the following association:
| Gene Identifier | Gene Name | Disease Identifier | Disease Name | Source Database | Source Score | Confidence Score |
| --- | --- | --- | --- | --- | ---  | ---  |
| ENSP00000004982 | HSPB6 | ICD10:N | ICD10:N | TIGA | MeanRankScore = 92 | 1.926 |
| ENSP00000004982 | HSPB6 | ICD10:N0 | ICD10:N0 | TIGA | MeanRankScore = 92 | 1.926 |
| ENSP00000004982 | HSPB6 | ICD10:N04 | ICD10:N04 | TIGA | MeanRankScore = 92 | 1.926 |
| ENSP00000004982 | HSPB6 | ICD10:N3 | ICD10:N3 | TIGA | MeanRankScore = 92 | 1.926 |
| ENSP00000004982 | HSPB6 | ICD10:N39 | ICD10:N39 | TIGA | MeanRankScore = 92 | 1.926 |
| ENSP00000004982 | HSPB6 | ICD10:N399 | ICD10:N399 | TIGA | MeanRankScore = 92 | 1.926 |
| ENSP00000004982 | HSPB6 | ICD10:root | ICD10:root | TIGA | MeanRankScore = 92  | 1.926 |

As you can see there is a cascading representation of the associated ICD10 codes of 'ICD10:N', 'ICD10:N0', 'ICD10:N04' and a second tree of 'ICD10:N3', 'ICD10:N39', 'ICD10:399'. 'ICD10:N', 'ICD10:N0', 'ICD10:N3', and 'ICD10:root' all do not correspond to any ICD10 codes and thus these lines were removed along with any other line in which an ICD10 code had one or two digits or was root following 'ICD10:'. Then for this particular association, the lowest unique tree leaves were taken in as associations with the Gene 'HSP86'. In this case that is 'ICD10:N04' and 'ICD10:N399'. The remaining line with 'ICD10:N39' was discarded as being a less specific referal than 'ICD10:N399'. Finally, the ICD10 codes were reformatted as necessary so that they follow the proper convention. There is a '.' following the regex string of [A-Z][0-9][0-9]. So, codes like 'ICD10:N399' were converted into the appropriate format of 'ICD10:N39.9' through insertion of the missing '.'.

The DISEASES datasource is composed of three datasets that were generated using three distinct methods: experiment (experimental data), knowledge (manual curation), and textmining. The specific dataset from which the data is from (i.e. 'experiments', 'knowledge', or 'textmining') is indicated by the provenance associated with each property value in the corresponding Disease, DiseaseGeneAssociation, Gene, or ICD10Code node. Also note that for each DiseaseGeneAssociation the link is between a Gene and a Disease represented by either a DOID or ICD10Code. Regardless of which the link is stored in the "diseaseID" property, which points to the corresponding Disease (in cases of DOID) or ICD10Code (in cases of ICD10 code) nodes.

### dcid Generation

Dcids for DiseaseGeneAssociation nodes were generated as either: 'bio/DOID_<trailing_DOID>_<geneSymbol> or 'bio/ICD10_<trailing_ICD10Code>_<geneSymbol> where the <trailing_DOID> and <trailing_ICD10Code> represent the id following the ':', <geneSymbol> represents the Gene's gene symbol. For example: `bio/DOID_0050177_SEMA3F` and `bio/DOID_0050736_SEMA3F`.

### License

This dataset is under a Creative Commons CC BY license.

### Dataset Documentation and Relevant Links

"DISEASES is a weekly updated web resource that integrates evidence on disease-gene associations from automatic text mining, manually curated literature, cancer mutation data, and genome-wide association studies." The full description of the dataset can be found [here](https://diseases.jensenlab.org/About). A description of the contents of the files and the links to download the DISEASE data as csv files can be found [here](https://diseases.jensenlab.org/Downloads).

The dataset is further documented in the following two studies:
- [DISEASES 2.0: a weekly updated database of disease–gene associations from text mining and data integration](https://academic.oup.com/database/article/doi/10.1093/database/baac019/6554833?login=false)
- [DISEASES: Text mining and data integration of disease-gene associations](https://www.sciencedirect.com/science/article/pii/S1046202314003831)

## About the import

### Artifacts

#### Scripts

##### Bash Script

[`download.sh`](scripts/download.sh) downloads the experimental, manually curated, and text mining data from DISEASES at Jensen Lab.
[`run.sh`](scripts/run.sh) converts raw data from DISEASES into csv files formatted for import into the Data Commons knowledge graph.
[`tests.sh`](scripts/tests.sh) runs standard tests on CSV + tMCF pairs to check for proper formatting.

##### Python Script

[`format_disease_jensen_lab.py`](scripts/format_disease_jensen_lab.py) parses the raw .tsv files with DISEASES at Jensen Lab into well formatted csv files with generated dcids and links to Gene and ICD10Code nodes.

#### tMCF Files

[`codingGenes-knowledge.tmcf`](tmcfs/codingGenes-knowledge.tmcf) contains the tmcf mapping to the csv of coding genes curated manually.

[`nonCodingGenes-knowledge.tmcf`](tmcfs/nonCodingGenes-knowledge.tmcf) contains the tmcf mapping to the csv of non-coding genes curated manually.

[`codingGenes-textmining.tmcf`](tmcfs/codingGenes-textmining.tmcf) contains the tmcf mapping to the csv of coding genes using textmining.

[`nonCodingGenes-textmining.tmcf`](tmcfs/nonCodingGenes-textmining.tmcf) contains the tmcf mapping to the csv of non-coding genes using textmining.

[`experiment.tmcf`](tmcfs/experiment.tmcf) contains the tmcf mapping to the csv of coding genes curated experimentally.

### Import Procedure

Download the most recent versions of DISEASES for experiment, manually curated, and text mining files:

```bash
sh download.sh
```

Generate the cleaned CSVs including splitting into seperate non-coding and coding genes into seperate csv files for each input file:

```bash
sh run.sh
```

### Tests

Run Data Commons's java -jar import tool to ensure that all schema used in the import is present in the graph, all referenced nodes are present in the graph, along with other warnings. Please note that empty tokens for some columns are expected as this reflects the original data. The imports create the linked Gene and ICD10Codes alongside the DiseaeGeneAssociation nodes that reference them. This resolves any concern about missing reference warnings concerning these node types by the test. Finally, there are not ICD10Codes associated with every disease, so this column is sometimes blank. Warnings concerning empty dcid references can therefore be ignored.

To run tests:

```bash
sh tests.sh
```

This will generate an output file for the results of the tests on each csv + tmcf pair
