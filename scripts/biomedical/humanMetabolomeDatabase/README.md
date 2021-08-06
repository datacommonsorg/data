# Importing HMDB Metabolome and Proteome Data

## Table of Contents

- [Importing HMDB Metabolome and Proteome Data](#importing-hmdb-metabolome-and-proteome-data)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Schema Overview](#schema-overview)
  - [About the import](#about-the-import)
  - [Examples](#examples)

## About the Dataset

### Download URL

The HMDB (Human Metabolome database) hosts a variety of datasets including, metabolites, proteins, diseases, pathways etc. The human metabolite and protein data can be downloaded from the official HMDB [webpage](https://hmdb.ca/downloads). The data is in xml format and had to be parsed into a csv version (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Overview

This directory stores the scripts used to convert the datasets obtained from HMDB into modified versions, for effective ingestion of data into the Data Commons knowledge graph.

The database links chemical, clinical and biochemical data of about 115,000 metabolites and multiple proteins. It also hosts multiple identifiers for various databases, linking the proteins and metabolites to multiple other data sources.
For the knowledge graph, two files are imported:

- <u>hmdb_metabolites.xml</u>: contains information on clinical and biochemical properties of metabolites. This HMDB metabolites file was first parsed into a csv file. Then, `ChEMBL` IDs for the metabolites were added by mapping metabolites in the hmdb dataset to those in Virtual Metabolic Human and Human-human1 datasets, which contain dcids. The remaining were mapped using the [bioservices package](https://bioservices.readthedocs.io/en/master/).

### Schema Overview

The schema representing metabolome and proteome data from HMDB is defined in [HMDB.mcf](https://raw.githubusercontent.com/suhana13/ISB-project/main/combined_list.mcf) and [HMDB_enum.mcf](https://raw.githubusercontent.com/suhana13/ISB-project/main/combined_list_enum.mcf). The tmcfs for each of the corresponding csv files can be found [here](https://github.com/suhana13/data/tree/add_hmdb_metabolites/scripts/biomedical/humanMetabolomeDatabase/tmcf).

The Metabolite entity is used to describe chemical substances which are intermediates or end products in a metabolic reaction. It has several text value properties, representing "humanMetabolomeDatabaseID", "monoIsotropicWeight", "iupacName", "chemicalName", "chemicalFormula", "inChIKey", "casRegistry", "simplifiedMolecularInputLineEntrySystem", "drugBankID", "chebiID", "pubChemCompoundID", "phenolExplorerCompoundID", "foodB", "knapsack", "chemSpiderID", "keggCompoundID", "metaCycID", "biggID", "metlinID", "proteinDataBankID", "drugLogP", and various enumeration classes, namely, "ChemicalCompoundCategoryEnum", "ChemicalCompoundParentEnum", "ChemicalCompoundSuperClassEnum", "ChemicalCompoundClassEnum", "ChemicalCompoundSubClassEnum", and "ChemicalCompoundMolecularFrameworkEnum".

The Protein entity is used to describe a class of nitrogenous organic compounds that are composed of large molecules called amino acids. It has several text value properties representing, "uniProtID", "genBankID", "geneCardID", "hgncID", "proteinGeneralFunction", "proteinSpecificFunction", "aminoAcidResidueNumber", and various enumeration classes, namely, "KeggProteinPathway", and "CellularCompartment".

- ### Notes and Caveats

The ChEMBL Id for the metabolites was missing, so it had to be generated using other databases, like VMH and HumanGEM-Human1, and also using the bioservices package. In addition, the proteins in hmdb were mapped to preexisting protein entities in Data Commons knowledge graph by querying multiple properties to identify the corresponding dcid. The dcid was manually currated in the handful of cases in which no matches were programatically found. Also, all the original data was formatted in xml format necesitating parsing which contributed to the total increase in runtime of the wrapper bash script.

- ### License

This data is freely available to all users. However, the commercial usage of the database requires explicit permission of the authors. More information on the HMDB license can be found [here](https://pubchem.ncbi.nlm.nih.gov/source/811).

## About the import

- ### Artifacts

- #### Scripts

[`hmdb_metabolite_xml_csv.py`](hmdb_metabolite_xml_csv.py)
[`format_metabolite.py`](format_metabolite.py)
[`hmdb_metabolite_add_chembl.py`](hmdb_metabolite_add_chembl.py)
[`format_hmdb_metabolites.py`](format_hmdb_metabolites.py)
[`hmdb_protein_xml_csv.py`](hmdb_protein_xml_csv.py)
[`format_hmdb_protein.py`](format_hmdb_protein.py)
[`format_hmdb_protein_metabolite.py`](format_hmdb_protein_metabolite.py)
[`format_hmdb_protein_pathway.py`](format_hmdb_protein_pathway.py)
[`parse_hmdb_go.py`](parse_hmdb_go.py)
[`format_hmdb_go.py`](format_hmdb_go.py)

## Examples

To generate the formatted csv file from xml:

```
python hmdb_metabolite_xml_csv.py hmdb_metabolites.xml

```

To process Virtual Metabolic Human metabolites and H data for next step (i.e. ChEMBL matching)

```
python format_metabolite.py recon-store-metabolites-1.tsv metabolites_vmh.csv hmdb_metabolites.csv

```

To add ChEMBL to hmdb metabolite data

```
python hmdb_metabolite_add_chembl.py metabolites.tsv metabolites_vmh.csv hmdb_metabolites.csv
```

To format hmdb metabolite data:

```
python format_hmdb_metabolites.py CHEMBL_HMDB_map.csv hmdb_metabolites_final.csv
```

To convert hmdb proteins xml to csv:

```
python hmdb_protein_xml_csv.py hmdb_proteins.xml
```

To format hmdb protein file -> Output: hmdb_protein.csv:

```
python format_hmdb_protein.py hmdb_p.csv
```

To format hmdb protein, metabolite association -> Output: hmdb_protein_metabolite.csv

```
python format_hmdb_protein_metabolite.py hmdb_protein.csv hmdb_pm_association.csv CHEMBL_HMDB_map.csv
```

To format hmdb protein kegg pathway -> Output: hmdb_protein_pathway.csv

```
python format_hmdb_protein_pathway.py protein_pathways.csv hmdb_protein.csv
```

To parse Gene Ontology information from hmdb xml file -> Output: hmdb_go.csv

```
python parse_hmdb_go.py hmdb_proteins.xml
```

To format hmdb Gene Ontology file -> Output: hmdb_go.csv

```
python format_hmdb_go.py hmdb_go.csv hmdb_protein.csv
```

OR
The user can simply run the entire bash script

```
wrapper_script.sh
```
