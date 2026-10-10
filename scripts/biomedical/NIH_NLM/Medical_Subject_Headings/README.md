# Importing Medical Subject Headings (MeSH) data from NCBI

## Table of Contents

1. [About the Dataset](#about-the-dataset)
   1. [Download Data](#download-data)
   2. [Overview](#overview)
   3. [Notes and Caveats](#notes-and-caveats)
   4. [dcid Generation](#dcid-generation)
   5. [License](#license)
2. [About the import](#about-the-import)
   1. [Artifacts](#artifacts)
      1. [Scripts](#scripts)
      2. [tMCF Files](#tmcf-files)
   2. [Import Procdeure](#import-procedure)
   3. [Tests](#tests) 

## About the Dataset

“The Medical Subject Headings (MeSH) thesaurus is a controlled and hierarchically-organized vocabulary produced by the National Library of Medicine. It is used for indexing, cataloging, and searching of biomedical and health-related information”. Data Commons includes the Concept, Descriptor, Qualifier, Supplementary Concept Record, and Term elements of MeSH as described [here](https://www.nlm.nih.gov/mesh/xml_data_elements.html). More information about the dataset can be found on the official National Center for Biotechnology (NCBI) [website](https://www.ncbi.nlm.nih.gov/mesh/). This dataset is updated on an annual basis on the first of January every year.
Pubchem is one of the largest reservoirs of chemical compound information. It is mapped to many other medical ontologies, including MeSH. More information about compound IDs and other properties can be found on their official [website](https://pubchemdocs.ncbi.nlm.nih.gov/compounds).

### Download Data

All the terminology referenced in the MeSH data can be downloaded in various formats [here](https://www.nlm.nih.gov/databases/download/mesh.html). The current xml files version can also be downloaded by running [`download.sh`](download.sh). To represent the entirity of the MeSH ontology in Biomedical Data Commons we download all for xml files from MeSH: `desc<year>.xml`, `pa<year>.xml`, `qual<year>.xml`, and `supp<year>.xml`. We also download from pubchem the mapping file between pubchem compound ids (CIDs) and corresponding MeSH Descriptor or Supplementary Concept Records MeSH unique ids (`CID-MeSH.csv`). All files required for this import can be downloaded by running[`download.sh`](download.sh)

### Overview

MeSH provides the vocabulary thesaurus used for indexing articles for PubMed. In addition, the scripts are used to map ther PubChem compound IDs to the MeSH descriptor and supplementary concept record. In this import we use the four MeSH xml files to define MeSH Concept, Descriptor, Qualifiers, Supplementary Concept Records, and Terms as individual nodes as well as maintaining mappings to each other. We also maintain links between these  data types to one other as indicated below. An overview on the MeSH Record Types can be found (here)[https://www.nlm.nih.gov/mesh/intro_record_types.html].

| Node Type | Property | Property Value Range\n(Out Link Node Type) |
| --- | --- | --- |
| MeSHConcept | preferredConcept | MeSHConcept |
| MeSHConcept | parent | MeSHDescriptor |
| MeSHConcept | hasMeSHQualifier | MeSHQualifier |
| MeSHDescpritor | sameAs | ChemicalCompund |
| MeSHDescriptor | mechanismOfAction | MeSHDescriptor |
| MeSHDescriptor | specializationOf | MeSHDescriptor |
| MeSHDescriptor | hasMeSHQualifier | MeSHQualifier |
| MeSHSupplementaryConceptRecord | mechanismOfAction | MeSHDescriptor |
| MeSHSupplementaryConceptRecord | parent | MeSHDescriptor |
| MeSHTerm | parent | MeSHConcept |

### Notes and Caveats

The total file size of all original downloaded files for this import is ~1.1 GB. The files from MeSH are in XML format and therefore use the python package `xml.etree.ElementTree` to read these files into pandas dataframes for further processing. Please, note that extracting the information from XML formatted tags and converting it into well-formatted csv involve a lot of computationally heavy steps, which depends on the RAM of the user's system. Please note that special care needs to be given when traversing through the XML tree to ensure that the properties at each level are associated with the appropriate MeSHTerm node type. As part of this process, we ended up making a seperate csv+tmcf pair for each node type from each file with an additional mapping csv+tmcf file pair to bring in mappings between node types as necessary. The total file size for all sixteen formatted csvs is ~135 MB. Finally, we also decided not to include `LexicalTag` or `IsPermutedTermYN` as properties for MeSHTerms from the `qual<year>.xml` file because for all Terms the property value was `NON` or `False` respectively, and thus these properties did not contain any additional information.

The `pa<year>.xml` file provided information on the pharmalogical action or mechanismOfAction of MeSHDescriptor and MeSHSupplementaryConceptRecord nodes. This provides pharmacological information about a subset of applicable MeSH records. Therefore, for MeSHDescriptor and MeSHSupplementaryConceptRecord nodes that were included in the `pa<year>.xml` as having mechanismOfAction that are connected MeShDescriptor nodes, we noted that these nodes were of Drug node type as well.

### dcid Generation
The dcids for all MeShRecordType nodes (MeSHConcept, MeSHDescriptor, MeSHQualifier, MeSHSupplementaryConceptRecord, and MeSHTerm) are generated using the mesh unique ids with the bio prefix: `bio/<MeSH_unique_id>`. For MeSH unique ids they are formatted as starting with a letter followed by a string of numbers with the identity of the starting letter indicating the MeSH record type. The mapping of MeSH record type by the first letter of its unique ID is indicated below. In addition to using the MeSH unique ID to generate the dcid, the unique id is recorded as the value of the `identifier` property for all MeSHRecordType nodes.

| Node Type | Starting Letter for MeSH unique ID |
| --- | --- |
| MeSHConcept | M |
| MeSHDescriptor | D |
| MeSHQualifier | Q | 
| MeSHSupplementaryConceptRecord | C |
| MeSHTerm | T |

The dcids for ChemicalCompounds were generated using the PubChem compound ID with the chem prefix: `chem/CID<PubChemCompoundID>` the PubChem Compound ID provided by PubChem is a string of numbers, therefore we added the specifier to the front of this id as part of the dcid to provide context. The PubChem Compound ID is also seperately stored as a string value to property `pubChemCompoundID`.

### License

Any works found on National Library of Medicine (NLM) Web sites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

## About the import

### Artifacts

#### Scripts

##### Bash Scripts

[`download.sh`](scripts/download.sh) downloads the desc, pa, qual, and supp xml files from MeSH as well as the CID-MeSH mapping file from pubchem.

[`run.sh`](scripts/run.sh) converts raw data from MeSH into csv files formatted for import into the Data Commons knowledge graph.

[`tests.sh`](scripts/tests.sh) runs standard tests on CSV + tMCF pairs to check for proper formatting.

##### Python Scripts

[`format_mesh_desc.py`](scripts/format_mesh_desc.py) converts the original xml into eight formatted csv files, which each can be imported alongside it's matching tMCF.

[`format_mesh_pa.py`](scripts/format_mesh_pa.py) converts the original csv file into two formatted csv files, which can be imported alongside it's matching tMCF.

[`format_mesh_qual.py`](scripts/format_mesh_qual.py) converts the original xml into four formatted csv files, which each can be imported alongside it's matching tMCF.

[`format_mesh_supp.py`](scripts/format_mesh_supp.py) converts the supplementary MeSH supplementary record file into a csv mapped to MeSH descriptor ID,
and it maps the MeSH supplementary records to pubchem compound IDs resulting in a second separate csv.

#### tMCF Files

The tMCF files that map each column in the corresponding CSV file to the appropriate property can be found [here](tmcf). They include:

[`mesh_desc_concept.tmcf`](tMCFs/mesh_desc_concept.tmcf) contains the tmcf mapping to the csv of concept nodes generated from the mesh desc file.

[`mesh_desc_concept_mapping.tmcf`](tMCFs/mesh_desc_concept_mapping.tmcf) contains the tmcf mapping to the csv of the links of concept nodes to descriptor nodes generated from the mesh desc file.

[`mesh_desc_descriptor.tmcf`](tMCFs/mesh_desc_descriptor.tmcf) contains the tmcf mapping to the csv of descriptor nodes generated from the mesh desc file.

[`mesh_desc_descriptor_mapping.tmcf`](tMCFs/mesh_desc_descriptor_mapping.tmcf) contains the tmcf mapping to the csv of descriptor nodes liks to parent (more general) descriptor nodes from the mesh desc file.

[`mesh_desc_qualifier.tmcf`](tMCFs/mesh_desc_qualifier.tmcf) contains the tmcf mapping to the csv of qualifier nodes generated from the mesh desc file.

[`mesh_desc_qualifier_mapping.tmcf`](tMCFs/mesh_desc_qualifier_mapping.tmcf) contains the tmcf mapping to the csv of desciptor nodes links to qualifier nodes generated from the mesh desc file.

[`mesh_desc_term.tmcf`](tMCFs/mesh_desc_term.tmcf) contains the tmcf mapping to the csv of term nodes generated from the mesh desc file.

[`mesh_desc_term_mapping.tmcf`](tMCFs/mesh_desc_term_mapping.tmcf) contains the tmcf mapping to the csv of the mappings of term nodes links to concept nodes from the mesh desc file.

[`mesh_pharmacological_action_descriptor.tmcf`](tMCFs/mesh_pharmacological_action.tmcf) contains the tmcf mapping to the csv of pharmacological actions of mesh descriptors to the appropriate mesh descriptor nodes from the mesh pa file.

[`mesh_pharmacological_action_record.tmcf`](tMCFs/mesh_pharmacological_action.tmcf) contains the tmcf mapping to the csv of pharmacological actions of mesh supplementary concept records to the appropriate mesh descriptor nodes from the mesh pa file.

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

The first step of `tests.sh` is to downloads Data Commons's java -jar import tool, storing it in a `tmp` directory. This assumes that the user has Java Runtime Environment (JRE) installed. This tool is described in Data Commons documentation of the [import pipeline](https://github.com/datacommonsorg/import/). The relases of the tool can be viewed [here](https://github.com/datacommonsorg/import/releases/). Here we download version `0.1-alpha.1k` and apply it to check our csv + tmcf import. It evaluates if all schema used in the import is present in the graph, all referenced nodes are present in the graph, along with other checks that issue fatal errors, errors, or warnings upon failing checks. Please note that empty tokens for some columns are expected as this reflects the original data. All referenced nodes are created as part of the same csv+tmcf import pair, therefore any Existence Missing Reference warnings can be ignored.

To run tests:

```bash
sh tests.sh
```

This will generate an output file for the results of the tests on each csv + tmcf pair
