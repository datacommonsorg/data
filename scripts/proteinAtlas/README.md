# Importing the Human Protein Atlas’ Tissue Atlas into Data Commons 

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

Data is available for downloading at [Protein Atlas Download](https://www.proteinatlas.org/about/download). (The main dataset used here is [normal_tissue.tsv](https://www.proteinatlas.org/download/normal_tissue.tsv.zip), the dataset to retrive \[Gene Name, UniProt Entry] pair is [proteinatlas.tsv.zip](https://www.proteinatlas.org/download/proteinatlas.tsv.zip).
 
### Overview

[Protein Tissue Atlas](https://www.proteinatlas.org/humanproteome/tissue) "contains information regarding the expression profiles of human genes both on the mRNA and protein level. The protein expression data from 44 normal human tissue types is derived from antibody-based protein profiling using immunohistochemistry." We create [ProteinOccurrence](https://datacommons.org/browser/HumanProteinOccurrence) class in Data Commons to show the distribution of proteins in different tissues and cell types with the protein expression level and the reliability score.

This directory stores all the scripts to generate the schema files [HumanCellTypeEnum.mcf](https://github.com/datacommonsorg/data/blob/master/schema/HumanCellTypeEnum.mcf), [HumanTissue.mcf](https://github.com/datacommonsorg/data/blob/master/schema/HumanTissue.mcf) and the data mcf file for this dataset. Here we only care about the protein distribution, thus the rows in [normal_tissue.tsv](https://www.proteinatlas.org/download/normal_tissue.tsv.zip) which cannot be linked to proteins were not imported.

### Notes and Caveats

The dataset [normal_tissue.tsv](https://www.proteinatlas.org/download/normal_tissue.tsv.zip) only has the gene name for each protein occurrence record, so we need to find the mapping from the gene name to the protein DCID in Data Commons to link to [Protein](https://datacommons.org/browser/Protein) nodes. The [proteinatlas.tsv](https://www.proteinatlas.org/download/proteinatlas.tsv.zip) dataset has gene name and UniProt entry for each protein occurrence record, and the [UniProt](https://www.uniprot.org/) can generate protein entry - protein DCID mapping. Thus we can have the gene name to protein DICD mapping. The details are in [Import Procedure](#import-procedure).   

### License

This dataset is available under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Please also see their [Disclaimer](https://www.proteinatlas.org/about/disclaimer) and [Licence & Citation](https://www.proteinatlas.org/about/licence)

### Dataset Documentation and Relevant Links

- Dataset website: [THe Human Protein Atlas - The Tissue Atlas](https://www.proteinatlas.org/humanproteome/tissue)

## About the import

### Artifacts

#### Scripts 

[parse_protein_atlas.py](https://github.com/datacommonsorg/data/blob/master/scripts/proteinAtlas/parse_protein_atlas.py) 

[parse_protein_atlas_test.py](https://github.com/datacommonsorg/data/blob/master/scripts/proteinAtlas/parse_protein_atlas_test.py) 

[generate_gene_to_uniprot_mapping.py](https://github.com/datacommonsorg/data/blob/master/scripts/proteinAtlas/generate_gene_to_uniprot_mapping.py.py)


### Import Procedure

#### Processing Steps 


To generate 'uniprot_list.txt' which contains all the UniProt entries and "gene_to_uniprot_list.txt" which contains the paired gene name and the UniProt entry list, run:

```bash
python3 generate_gene_to_uniprot_mapping.py -f proteinatlas.tsv --uniprot uniprot_list.txt --gene_to_uniprot gene_to_uniprot_list.txt 
```
Then upload the file uniprot_list.txt containing UniProt entries separated by space to [UniProt Retrieve/ID mapping](https://www.uniprot.org/uploadlists/) to generate the UniProt \[Entry, Entry Name] pairs and save to file [uniprot_to_dcid.tsv](https://github.com/datacommonsorg/data/blob/master/scripts/proteinAtlas/uniprot_to_dcid.tsv). The pair example is \['Q96GF1', 'RN185_HUMAN']. The UniProt Entry Name is the DCID for protein instances in Data Commons. Thus we can create the mapping from gene name to protein DCID.

To generate the data MCF file and enumeration files, run:

```bash
python3 parse_protein_atlas.py --database normal_tissue.tsv -g gene_to_uniprot_list -u uniprot_to_dcid.tsv -m ProteinAtlasData.mcf --tissue_mcf HumanTissueEnum.mcf --cell_mcf HumanCellTypeEnum.mcf
```

To test the script, run:

```bash
python3 parse_protein_atlas_test.py
```
