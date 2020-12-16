# Importing the ExPASy's Antibody Dataset ABCD into Data Commons 

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

Data is available for downloading by contacting ExPASy through [ExPASy Helpdesk form](https://web.expasy.org/contact). We contacted them and are granted the permission to import and share their dataset via Data Commons Knowledge Graph.
 
### Overview

"[The ABCD (for AntiBodies Chemically Defined) database](https://web.expasy.org/abcd/) is a repository of sequenced antibodies, integrating curated information about the antibody and its antigen with cross-links to standardized databases of chemical and protein entities." as in the paper [The ABCD database: a repository for chemically defined antibodies](https://academic.oup.com/nar/article/48/D1/D261/5549708). "It was developed by the [Geneva Antibody Facility](https://www.unige.ch/medecine/antibodies/) at the University of Geneva, in collaboration with the [CALIPHO](https://www.sib.swiss/amos-bairoch-lydie-lane-group) and [Swiss-Prot](https://www.sib.swiss/alan-bridge-group) groups at [SIB Swiss Institute of Bioinformatics](https://www.sib.swiss/)" as in the website.


This directory stores all the scripts to generate the data mcf file for this dataset. Currently we only imported the antibodies of which the antigen is protein type and linked the antibody nodes to existing [Protein](https://datacommons.org/browser/Protein) nodes in Data Commons. In the future we will also import the antibodies of which the antigen is chemicals and other types. The antigens which are chemicals are referred to [ChEBI](https://www.ebi.ac.uk/chebi/) database.

### Notes and Caveats

The dataset ABCD_v8.txt only has [UniProt](https://www.uniprot.org/) Entry for each antibody record, so we need to find the mapping from the entry to the protein DCID in Data Commons, which is the 'Entry Name' at [UniProt](https://www.uniprot.org/), to link to [Protein](https://datacommons.org/browser/Protein) nodes. The [UniProt](https://www.uniprot.org/) can generate \[protein entry - protein DCID\] mapping and the details are in [Import Procedure](#import-procedure).   


### Dataset Documentation and Relevant Links

- Dataset website: [The ABCD (for AntiBodies Chemically Defined) database](https://web.expasy.org/abcd/)
- Reference literature: [The ABCD database: a repository for chemically defined antibodies](https://academic.oup.com/nar/article/48/D1/D261/5549708)

## About the import

### Artifacts

#### Scripts 

[parse_abcd.py](https://github.com/datacommonsorg/data/blob/master/scripts/antibodyABCD/parse_abcd.py) 

[parse_abcd_test.py](https://github.com/datacommonsorg/data/blob/master/scripts/antibodyABCD/parse_abcd_test.py) 

[generate_uniprot_entries.py](https://github.com/datacommonsorg/data/blob/master/scripts/antibodyABCD/generate_uniprot_entries.py)


### Import Procedure

#### Processing Steps 


To generate [uniprot_list.txt](https://github.com/datacommonsorg/data/blob/master/scripts/antibodyABCD/uniprot_list.txt) which contains all the UniProt entries, run:

```bash
python3 generate_uniprot_entries.py -f ABCD_v8.txt --uniprot uniprot_list.txt
```
Then upload the file uniprot_list.txt containing UniProt entries separated by space to [UniProt Retrieve/ID mapping](https://www.uniprot.org/uploadlists/) to generate the UniProt \[Entry, Entry Name] pairs and save to file [uniprot_to_dcid.tsv](https://github.com/datacommonsorg/data/blob/master/scripts/proteinAtlas/uniprot_to_dcid.tsv). The paired example is \['Q96GF1', 'RN185_HUMAN']. The UniProt Entry Name is the DCID for protein instances in Data Commons.

[uniprot_list.txt](https://github.com/datacommonsorg/data/blob/master/scripts/antibodyABCD/uniprot_list.txt) will be used by [parse_abcd.py](https://github.com/datacommonsorg/data/blob/master/scripts/antibodyABCD/parse_abcd.py).
To generate the data MCF file and enumeration files, run:

```bash
python3 parse_abcd.py --data_mcf ABCD_v8.txt -u uniprot_to_dcid.tsv -m AntibodyABCDData.mcf
```

To test the script, run:

```bash
python3 parse_abcd_test.py
```
