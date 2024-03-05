# Importing Medical Subject Headings (MeSH) data from NCBI

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
   2. [Import Procdeure](#import-procedure)
   3. [Tests](#tests) 

## About the Dataset

“The Medical Subject Headings (MeSH) thesaurus is a controlled and hierarchically-organized vocabulary produced by the National Library of Medicine. It is used for indexing, cataloging, and searching of biomedical and health-related information”. Data Commons includes the Concept, Descriptor, Qualifier, Supplementary Record and Term elements of MeSH as described [here](https://www.nlm.nih.gov/mesh/xml_data_elements.html). More information about the dataset can be found on the official National Center for Biotechnology (NCBI) [website](https://www.ncbi.nlm.nih.gov/mesh/).
Pubchem is one of the largest reservoirs of chemical compound information. It is mapped to many other medical ontologies, including
MeSH. More information about compound IDs and other properties can be found on their official [website](https://pubchemdocs.ncbi.nlm.nih.gov/compounds).

### Download Data

All the terminology referenced in the MeSH data can be downloaded in various formats [here](https://www.nlm.nih.gov/databases/download/mesh.html). The current xml files version can also be downloaded by running [`download.sh`](download.sh). For the purpose of mapping all mesh terms with each other, two xml files are used, namely: `desc2022.xml` and `supp2022.xml`.
The csv version of the file containing PubChem Compound ID and names can also be downloaded by running[`download.sh`](download.sh)

### Overview

This directory stores the scripts used to convert the xml obtained from the NCBI webpage into five different csv files, each describing the relation between supplementary records, concepts, terms, qualifiers and descriptors, and generating dcids for each.
The MeSH data stores the vocabulary thesaurus used for indexing articles for PubMed. In addition, the scripts are used to map ther PubChem compound IDs to the MeSH descriptor and supplementary record IDs, joining on MeSH supplementary record name/PubChem compoundID.

- For mapping the MeSH descriptor ID with the MeSH supplementary record ID, the [supplementary file](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/supp2022.xml) is used.
- For mapping the MeSH descriptor ID with each of the three other IDs: concept ID, term ID, qualifier ID, the [descriptor file](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2022.xml) is used.
- For mapping the PubChem compound ID with the MeSH supplementary record and descriptor ID, the [pubchem file](https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-MeSH) is used.

### Notes and Caveats

The main main file and the mesh supplementary file are both XML formatted. In addition, they're about 300-600 GB worth of storage. This is one the major contributors of extended run time for the scripts. Extracting the information from XML formatted tags and converting it into well-formatted csv involve a lot of computationally heavy steps, which depends on the RAM of the user's system.

To run the script [`format_mesh.py`](format_mesh.py), the user requires the `mesh-descriptor.xml` file, which outputs five different csv files, each relating to descriptor, concept, qualifier and term.

To run the script [`format_mesh_record.py`](format_mesh_record.py), the user requires the `mesh_record.xml` file and the `mesh-pubchem.csv` file which maps the record to descriptor and to the pubchem compound ID, and outputs two csv files one for the supplementary records and one with the mappings between mesh and pubchem. Here, the goal is to map the mesh terms to the pubchem database of compounds. This is accomplished by mapping the mesh record name to the pubchem compound name. In addition, each mesh entity has a descriptor ID which is in turn linked to mesh suplementary record ID, and thus ultimately linked to pubchem compound ID. 


### dcid Generation

### License

Any works found on National Library of Medicine (NLM) Web sites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

### Dataset Documentation and Relevant Links

## About the import

### Artifacts

#### Scripts

##### Bash Scripts

[`download.sh`](scripts/download.sh) downloads the desc, pa, qual, and supp xml files from MeSH as well as the CID-MeSH mapping file from pubchem.

[`run.sh`](scripts/run.sh) converts raw data from MeSH into csv files formatted for import into the Data Commons knowledge graph.

[`tests.sh`](scripts/tests.sh) runs standard tests on CSV + tMCF pairs to check for proper formatting.

##### Python Scripts

[`format_mesh_desc.py`](scripts/format_mesh_desc.py) converts the original xml into five formatted csv files, which each can be imported alongside it's matching tMCF.

[`format_mesh_pan.py`](scripts/format_mesh_pa.py) converts the original csv file into one formatted csv file, which can be imported alongside it's matching tMCF.

[`format_mesh_qual.py`](scripts/format_mesh_qual.py) converts the original xml into four formatted csv files, which each can be imported alongside it's matching tMCF.

[`format_mesh_supp.py`](scripts/format_mesh_supp.py) converts the supplementary MeSH supplementary record file into a csv mapped to MeSH descriptor ID,
and it maps the MeSH supplementary records to pubchem compound IDs resulting in a second separate csv.

#### tMCF Files

The tMCF files that map each column in the corresponding CSV file to the appropriate property can be found [here](tmcf). They include:

[`mesh_desc_concept.tmcf`](tMCFs/mesh_desc_concept.tmcf) contains the tmcf mapping to the csv of concept nodes generated from the mesh desc file.

[`mesh_desc_descriptor.tmcf`](tMCFs/mesh_desc_descriptor.tmcf) contains the tmcf mapping to the csv of descriptor nodes generated from the mesh desc file.

[`mesh_desc_qualifier.tmcf`](tMCFs/mesh_desc_qualifier.tmcf) contains the tmcf mapping to the csv of qualifier nodes generated from the mesh desc file.

[`mesh_desc_qualifier_mapping.tmcf`](tMCFs/mesh_desc_qualifier_mapping.tmcf) contains the tmcf mapping to the csv of descriptor qualifier mappings generated from the mesh desc file.

[`mesh_desc_term.tmcf`](tMCFs/mesh_desc_term.tmcf) contains the tmcf mapping to the csv of term nodes generated from the mesh desc file.

[`mesh_pharmacological_action.tmcf`](tMCFs/mesh_pharmacological_action.tmcf) contains the tmcf mapping to the csv of pharmacological actions from the mesh pa file.

[`mesh_pubchem_mapping.tmcf`](tMCFs/mesh_pubchem_mapping.tmcf) contains the tmcf mapping to the csv of pubchem compound CIDs to MeSH Supplementary Records from the `CID-MESH.csv` and the mesh supp file.

[`mesh_qual_concept.tmcf`](tMCFs/mesh_qual_concept.tmcf) contains the tmcf mapping to the csv of concept nodes generated from the mesh qual file.

[`mesh_qual_concept_mapping.tmcf`](tMCFs/mesh_qual_concept_mapping.tmcf) contains the tmcf mapping to the csv of mappings of concept nodes to other mesh node types generated from the mesh qual file.

[`mesh_qual_qualifier.tmcf`](tMCFs/mesh_qual_qualifier.tmcf) contains the tmcf mapping to the csv of qualifier nodes generated from the mesh qual file.

[`mesh_qual_term.tmcf`](tMCFs/mesh_qual_term.tmcf) contains the tmcf mapping to the csv of term nodes generated from the mesh qual file.

[`mesh_record.tmcf`](tMCFs/mesh_record.tmcf) ontains the tmcf mapping to the csv of supplementary record nodes generated from the mesh supp file.

### Import Procedure

Download the most recent versions of all mesh files (desc, pa, qual, and supp) and the pubchem file that maps CID to MeSH Supplementary Records:

```bash
sh download.sh
```

Generate the cleaned CSVs including splitting into seperate non-coding and coding genes into seperate csv files for each input file:

```bash
sh run.sh
```

### Tests

Run Data Commons's java -jar import tool to ensure that all schema used in the import is present in the graph, all referenced nodes are present in the graph, along with other warnings. Please note that empty tokens for some columns are expected as this reflects the original data.
To run tests:

```bash
sh tests.sh
```

This will generate an output file for the results of the tests on each csv + tmcf pair
