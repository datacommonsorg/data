# Importing the PharmGKB data - Genes, Drugs, Chemicals and Other Mappings

## Table of Contents

- [Importing PharmGKB](#importing-pharmgkb)
  - [About the Dataset](#about-the-dataset)
    - [Download Data](#download-data)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [Files](#files)
    - [Import Procedure](#import-procedure)
      - [Download](#download)
      - [Run Scripts](#run-scripts)

## About the Dataset

### Download Data

The zip files for drugs, chemicals, genes, and relationships can be found [here](https://www.pharmgkb.org/downloads). The latest version of the data can be directly downloaded from their website.

### Overview

This dataset brings in various PharmGKB annotated biological entities including:

- genes
- drugs
- chemicals
- variant
- phenotypes

<br> </br>
These entities, in turn, contain links to other databases including but not limited to NCBI, HGNC, Ensembl, HMDB, KEGG, PubChem, UMLS, DrugBank, ChemSpider,and MeSH. In addition, this dataset brings in the interactions between the entities, including:

- Chemical - Chemical Associations
- Chemical - Gene Associations
- Chemical - Genetic Variant Associations
- Gene - Gene Associations
- Gene - Genetic Variant Associations
- Genetic Variant - Genetic Variant Associations
- Disease - Disease Associations
- Disease - Gene Assocations
- Disease - Genetic Variant Assocations

### Notes and Caveats

- For drugs and chemicals, the creators of PharmGKB database condensed all cross-references in one column. However, for bringing the data into the knowledge graph, we had to explode the column containing cross-references based on which database it is being pulled from. In addition, the primary annotation for all chemical compounds and drugs is their pharmgkb identifier. However, since datacommons aims for coherence and interconnectedness between all different databases, we use the Pubchem Compound Id as the dcid for the compounds. Our next fall back options are MeSH, Chembl and ATC codes. For compounds that do not map to any of these identifiers, we used the chemical names as their dcids.

- In `relationships.tsv`, some of the diseases are missing PubChem Compound identifiers. Similarly, some variants are missing rsIDs. These entities were omitted from the import since they don't reference any existing node on datacommons and lack other property values.

### License

PharmGKB is under a Creative Commons Attribution-ShareAlike 4.0 International License. More information on that can be viewed [here](https://www.pharmgkb.org/page/dataUsagePolicy).
More information about the license can be viewed [here](https://creativecommons.org/licenses/by-sa/4.0/).

## About the import

### Artifacts

#### Scripts

- ['format_genes.py'](format_genes.py)
- ['format_chemicals.py'](format_chemicals.py)
- ['format_drugs.py'](format_drugs.py)
- ['format_variants.py'](format_variants.py)
- ['format_relationships.py'](format_relationships.py)

#### Files

- `chemicals.tsv`
- `drugs.tsv`
- `genes.tsv`
- `phenotypes.tsv`
- `relationships.tsv`
- `variants.tsv`
- `chemicals_pkgb_dict.csv`
- `drugs_pkgb_dict.csv`

### Import Procedure

#### Download

For the ease of downloading all files and moving them to subsequent folders, the user can just run the `download.sh` script:

```bash
bash download.sh
```

For generating formatted files, run the following bash script:

```bash
bash run.sh
```
