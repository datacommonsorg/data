# Importing the PharmGKB data - Genes, Drugs, Chemicals and Other Mappings

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Download Data](#download-data)
    2. [Database Overview](#database-overview)
    3. [Schema Overview](#schema-overview)
       1. [New Schema](#new-schema)
       2. [dcid Generation](#dcid-generation)
       3. [Edges](#edges)
    4. [Notes and Caveats](#notes-and-caveats)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
       1. [Scripts](#scripts)
       2. [tMCFs](#tmcfs)
       3. [Mapping Files](#mapping-files)
    2. [Import Procedure](#import-procedure)
    3. [Test](#test)

## About the Dataset

### Download Data

The zip files for drugs, chemicals, genes, and relationships can be found [here](https://www.pharmgkb.org/downloads). The latest version of the data can be directly downloaded from their website.

### Database Overview

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

In this import we will process the following files:

* Primary Data
  *`chemicals.tsv`
  *`drugs.tsv`
  * `genes.tsv`
  * `phenotypes.tsv`
  * `variants.tsv`
* Variant, Gene and Drug Relationship Data
  * `relationships.tsv`

### Schema Overview

### Notes and Caveats

PharmGKB has its own identifier - PharmGKB ID - that distinguishes each entity in its database. Therefore, as part of the import process we had to map chemicals, drugs, diseases, genes, genetic variants, and phenotypes to existing nodes in the graph. For chemicals and drugs this was done by using the corresponding PubChem Compound Identifier (CID), which is the preferred dcid method for these entities in Data Commons. In cases in which the chemical or drug was too general to have a specific CID (e.g. 'estrogens') then the name was used to generate the dcid. Mapping files between chemical and drugs PharmGKB IDs and the dcids used to represent this data were generated as part of processing the primary data: [`chemicals_pharmgkbId_to_dcid.csv`](mapping_files/chemicals_pharmgkbId_to_dcid.csv) and [`drugs_pharmgkbId_to_dcid.csv`](mapping_files/drugs_pharmgkbId_to_dcid.csv). These files were used to generate the chemical compound association dcids and the edges to the corresponding ChemicalCompound and Drug nodes as part of the relationships data import. Phenotypes were provided with the corresponding MeSH Descriptor ID, which was used to map them to existing MeSHDescriptor nodes in the graph. Diseases were also mapped to existing MeSHDescriptor nodes by matching on names of exisiting MeSHDescrptor nodes in the graph using the Data Commons API. In cases, in which no match was found using the API, these cases were manually mapped the PharmGKBId to the MeSHDescriptor dcid using the provided disease name. These mappings are represented in the [`diseases_pharmgkbId_to_dcid.csv`](mapping_files/diseases_pharmgkbId_to_dcid.csv). This information was used to generate the disease association dcids and the edges to MeSHDescriptor nodes. PharmGKB provided the gene symbol for all genes, so we were able to successfully map this data to existing data commons Gene nodes. Finally, for genetic variants we used the rsIDs, which were represented as the name to map them to existing GeneticVariant nodes. For the primary data all names were rsIDs. However, for the variants in the relationship file, sometimes the name for the variant participating in the relationship was not attributed to a single variant (e.g. 'CYB5R3 deficiency'). In these cases these variant relationships were excluded in the import.

For drugs and chemicals the PharmGKB database condensed all cross-references in one column. As part of the cleaning this column was exploded so that each database was mapped to a distinct property represented as it's own column. In addition, the relationships data contains information on haplotypes. As haplotypes are not represented in the Data Commons graph these relationships were not included in the important. Furthermore, although all relationship types are represented into a single input file as part of cleaning up this file we expanded this into nine cleaned csv output files with each file representing each type of unique association. This is necessary to map the data appropriately to nodes and properties in the corresponding tMCF files.

### License

PharmGKB is under a Creative Commons Attribution-ShareAlike 4.0 International License. More information on that can be viewed [here](https://www.pharmgkb.org/page/dataUsagePolicy).
More information about the license can be viewed [here](https://creativecommons.org/licenses/by-sa/4.0/).

###  Dataset Documentation and Releavant Links

[PharmGKB](https://www.pharmgkb.org/) is partnered with CPIC, PharmVar, PharmCat, PGRN, ClinGen and Global Core Biodata Resource. Data from PharmGKB can be downloaded [here](https://www.pharmgkb.org/downloads). In addition to downloading the data directly, PharmGKB has their own [REST API](https://api.pharmgkb.org/swagger/). Additional updates are released on their [blog](https://blog.clinpgx.org/).

To cite PharmGKB please use the following publications:
M. Whirl-Carrillo<sup>1</sup>, R. Huddart<sup>1</sup>, L. Gong, K. Sangkuhl, C.F. Thorn, R. Whaley and T.E. Klein. ["An evidence-based framework for evaluating pharmacogenomics knowledge for personalized medicine"](https://pubmed.ncbi.nlm.nih.gov/34216021/). *Clinical Pharmacology & Therapeutics* (2021) Sep;110(3):563-572.

<sup>1</sup>co-first authors

PMID: 34216021
PMCID: PMC8457105
DOI: 10.1002/cpt.2350

M. Whirl-Carrillo, E.M. McDonagh, J.M. Hebert, L. Gong, K. Sangkuhl, C.F. Thorn, R.B. Altman and T.E. Klein. ["Pharmacogenomics knowledge for personalized medicine"](https://pubmed.ncbi.nlm.nih.gov/22992668/). *Clinical Pharmacology & Therapeutics* (2012) Oct;92(4):414-7.

PMID: 22992668
PMCID: PMC3660037
DOI: 10.1038/clpt.2012.96

Additional information regarding citing PharmGKB can be found [here](https://www.pharmgkb.org/page/citingPharmgkb).


## About the Import

### Artifacts

#### Scripts

- ['format_chemicals.py'](scripts/format_chemicals.py)
- ['format_drugs.py'](scripts/format_drugs.py)
- ['format_genes.py'](scripts/format_genes.py)
- ['format_phenotypes.py'](scripts/format_phenotypes.py)
- ['format_variants.py'](scripts/format_variants.py)
- ['format_relationships.py'](scripts/format_relationships.py)

#### tMCFs

#### Mapping Files

### Import Procedure

Download the most recent versions of NCBI Taxonomy data:

```bash
sh download.sh
```

Generate the enum schema MCF & formatted CSV:

```bash
sh run.sh
```


### Test 

To run tests:

```bash
sh tests.sh
```
