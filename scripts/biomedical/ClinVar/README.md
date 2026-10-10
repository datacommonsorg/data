
# Importing ontology dataset of molecular interaction from the European Bioinformatics Institute (EMBL-EBI)

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

txt file is available for download from
https://www.ebi.ac.uk/ols/ontologies/mi. It refers to http://psidev.info/groups/molecular-interactions. 

### Overview

This directory stores all scripts used to import the ontology dataset from the European Bioinformatics Institute (EMBL-EBI). It contains the controlled vocabularies, which are the standard terms used in molecular interaction, of the Proteomic Standard Initiative (PSI).  

Here we only import the three subsets of the ontologies: "interaction detection method", "interaction type" and "database citation", which are commonly used in protein-protein interactions. The ontologies dictionary has a tree structure. Note here that one parent node can have multiple child nodes and one child node can have multiple parent nodes as well. We firstly build the tree, then collect the nodes of the three subtrees separately.  

### Notes and Caveats

The database file (mi.owl) uses "is_a" and "part_of" as the relation property to connect the child node to the parent node, however we don't distinguish these two and a property "specializationOf" is used for the child-parent connection.

We make each term as an enumeration node of three subtrees with root nodes as: "database citation", "interaction detection method", and "interaction type". There are two main concerns that we didn't import all the nodes. First, we focus on the ontologies in protein-protein interaction and these three categories are the most commonly used. Secondly, to avoid general terms from another ontology from polluting the Data Commons schema. 

We also left out the properties named "synonym", "subset", "created_by" and "creation_date" which contain the data that don't play important roles in our nodes of protein-protein interaction currently. If needed we will import these properties in the future. Property "identifier" of each enumeration instance contains a PSI-MI identifier. 

### License

The data is published by Human Proteome Organization (HUPO) Proteomics Standards Initiative. http://psidev.info/groups/controlled-vocabularies, http://psidev.info/groups/molecular-interactions, and was downloaded from https://www.ebi.ac.uk/ols/ontologies/mi.

### Dataset Documentation and Relevant Links

- Documentation: http://psidev.info/groups/molecular-interactions
- Data Visualization UI: https://www.ebi.ac.uk/ols/ontologies/mi

## About the import

### Artifacts

#### New Enumeration

InteractionTypeEnum, InteractionDetectionMethodEnum, InteractionSourceEnum.

#### New Properties

goID, residID, psimiID 

#### Schema MCFs

[CoumpoundSchema.mcf](https://github.com/datacommonsorg/schema/blob/main/biomedical_schema/chemical_compound.mcf) 

#### Cleaned Data

[BioOntologySchemaEnum.mcf](https://github.com/datacommonsorg/schema/new/main/biomedical_schema/BioOntologySchemaEnum.mcf) 

#### Scripts 

parse_ebi.py

### Import Procedure

#### Processing Steps 

To generate 'BioOntologySchemaEnum.mcf' which contains all the schemas and "psimi2dcid.txt" which contains paired PSI-MI identifiers and DCID (../proteinInteractionMINT/parse_mint.py needs to use this file to refer to the corresponding Enum instance by DCID), run:

```bash
python3 parse_ebi.py -f mi.owl -new_source new_source.txt
```

To test the script, run:

```bash
python3 parse_ebi_test.py
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
and the function get_references in parse_ebi.py should handle the new source correspondingly.

#### Parsing Steps Overview

1. build the tree by the psi-mi number. A dictionary {psi-mi: node} is used to access nodes as well. 
2. nodes of three subtrees will be imported, and roots of the subtrees are:
- "id: MI:0001 name: interaction detection method" 
- "id: MI:0190 name: interaction type"  
- "id: MI:0444 name: database citation" 

  Depth-first search was run on each root to collect the node values separately.

3. save the nodes in the three sets to the corresponding enumeration schema





# Database Overview
[dbSNP](https://www.ncbi.nlm.nih.gov/snp/?cmd=search) is an NCBI public-domain database of a broad array of simple genetic variations. It "contains human single nucleotide variations, microsatellites, and small-scale insertions and deletions along with publication, population frequency, molecular consequence, and genomic and RefSeq mapping information for both common variations and clinical mutations." Any type of variation is accepted including "single-base nucleotide substitutions (also known as single nucleotide polymorphisms or SNPs), small-scale multi-base deletions or insertions (also called deletion insertion polymorphisms or DIPs), and retroposable element insertions and microsatellite repeat variations (also called short tandem repeats or STRs)." The database is updated semi-annually to include new submissions. 

dbSNP previously accepted, maintained, and supported genetic variants from any and all organisms, however, this ended in December 2018. Now, it only supports new submissions for genetic variants in humans. We have included all human genetic variants from dbSNP in Data Commons supporting both genome assemblies hg19 and hg38.

## Database Download
Data was downloaded as VCFs using the [FTP download](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/) functionality. Files for both [hg19](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz) and [hg38](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.38.gz) were downloaded, cleaned, and ingested.

# Generation of MCFs

## scripts used
[format_dbSNP_GenVarSource_enum_schema.py](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_GenVarSource_enum_schema.py)

[format_dbSNP_alt_ID_database_property_schema.py](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_alt_ID_database_property_schema.py)


## Generation of schema by script
The schema for both the data sources for the allele frequencies of genetic variants and the databases with alternative IDs for genetic variants were generated using scripts. The GenVarSourceEnum for data sources of allele frequencies is generated using [format_dbSNP_GenVarSource_enum_schema.py](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_GenVarSource_enum_schema.py). The GeneticVariant properties for alternative IDs is generated using [format_dbSNP_alt_ID_database_property_schema.py](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_alt_ID_database_property_schema.py).
