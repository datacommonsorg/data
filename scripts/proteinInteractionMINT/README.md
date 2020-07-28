# Importing protein-protein interaction dataset from the Molecular INTeraction database (MINT)

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [License](#license)
    5. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)


## About the Dataset

### Download URL

The data can be downloaded at [MINT Download](https://mint.bio.uniroma2.it/index.php/download/)

The downloaded data is tab-separated format. 

### Overview

This directory stores all scripts used to import datasets from the Molecular INTeraction database (MINT). MINT contains publicly available protein-protein interactions and uses the Molecular Interaction Ontology of the Proteomics Standard Initiative (PSI-MI). 

A protein-protein interaction instance connects to partipant proteins through property "interactingProtein", connects to detection methods through property "interactionDetectionMethod", connects to interaction type through property "interactionType", connects to the source database through property "interactionSource", connects to related publications through property "references" and connects to related database records through property "identifier". The objects of "interactionType", "interactionDetectionMethod" and "interactionSource" are enumeration instances from EMBL-EBI Molecular Interaction Ontology database. The objects of "interactingProtein" are protein instances from UniPort.

#### Example Nodes in Data Commons

[ProteinProteinInteraction](https://datacommons.org/browser/ProteinProteinInteraction) 

[AGO2_HUMAN_PABP1_HUMAN](https://datacommons.org/browser/bio/AGO2_HUMAN_PABP1_HUMAN) 

### Notes and Caveats

The dataset contains information for the interaction and the participant proteins. A full interaction example from the website: [MINT-4409840](https://mint.bio.uniroma2.it/index.php/detailed-curation/?id=MINT-4409840). The features of each participant such as "Biological role", "Interactor type" are not included in the downloadable database thus we didn't import these features to Data Commons.

There are 133,167 records in the MINT database. Here we imported 129,585 records to Data Commons. The 3,582 records that we didn't import have problematic protein identifiers that we cannot connect them to UniProt protein instances right now.

### License

Licata, Luana, Leonardo Briganti, Daniele Peluso, Livia Perfetto, Marta Iannuccelli, Eugenia Galeota, Francesca Sacco et al. "MINT, the molecular interaction database: 2012 update." Nucleic acids research 40, no. D1 (2012): D857-D861.

### Dataset Documentation and Relevant Links

- Documentation: [MINT, the molecular interaction database: 2012 update](https://academic.oup.com/nar/article/40/D1/D857/2903552)
- Data website: [MINT](https://mint.bio.uniroma2.it/)

## About the import

### Artifacts

#### Scripts 

parse_ebi.py 

parse_ebi_test.py 

### Import Procedure

#### Processing Steps 

To generate the data mcf from MINT, run:

```bash
python3 parse_mint.py -f mint_database -p psimi2dcid.txt
```
If new reference sources which are not properties in dcs occur, 'new_source.txt' containing such information will be generated as well. 

Somes cases were not imported into the KG due to the lack of UniProt ID or the incorrect dcid format. To generate the files containing the information for the failed cases, run:  

```bash
python3 parse_mint.py -f mint_database -p psimi2dcid.txt -o True
```
The interaction information of the records which don't have UniProt name will be saved to 'no_uniprot_cases.txt',  which don't have correct DCIDs will be saved to 'wrong_dcid_cases.txt'.

To do the unit test, run:
```bash
python3 parse_mint_test.py
```

#### Post-Processing Steps 

If new reference sources which are not properties in dcs occur, 'new_source.txt' containing such information will be generated. For example: 

```
references
pubMedID: 1007323
goID: 30234
```

If this is the case, new properties should be created for the new sources and added to data/schema/CompoundSchema.mcf, such as:

```
Node: dcid:pubMedID
typeOf: schema:Property
name: "pubMedID"
rangeIncludes: schema:Text
domainIncludes: dcs:ChemicalCompound
description: "Identifier for reference paper on PubMed."
url: "https://pubmed.ncbi.nlm.nih.gov/"
```
and the function get_references in parse_ebi.py should handle the new source correspondingly. The same steps for identifiers and confidence score.
