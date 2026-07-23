# Importing drug data from STITCH

## Table of Contents

- [Importing data from STITCH](#importing-data-from-stitch)
  - [About the Dataset](#about-the-dataset)
    - [Download Data](#download-data)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [Files](#files)
     - [Schema Artifacts](#schema)
       - [tMCF Files](#tmcf-files)
       - [Output Schema MCF Files](#output-schema-mcf-files)
  - [Examples](#examples)
    - [Run Tests](#run-testers)
    - [Import](#import)

# About the Dataset
[STITCH](http://stitch.embl.de/cgi/input.pl?UserId=f68rPwGhmUhl&sessionId=URI01tKFfMAQ) ('Search Tool for Interacting Chemicals') is one of the largest and most used publicly available databases supported by EMBL (European Molecular Biology Laboratory). It contains around 500,000 drugs and 9.6 million proteins and that accounts for 1.6 billion interactions. This includes both drug-drug and drug-protein interactions. "The interactions include direct (physical) and indirect (functional) associations; they stem from computational prediction, from knowledge transfer between organisms, and from interactions aggregated from other (primary) databases." The last time the database was updated was in 2016. 

### Download Data
The majority of the data was downloaded as TSVs from the [STITCH website](http://stitch.embl.de/cgi/download.pl?UserId=f68rPwGhmUhl&sessionId=FgUl09kij1IU&species_text=Homo+sapiens). Files for [sources.tsv](http://stitch.embl.de/download/chemical.sources.v5.0.tsv.gz), [inchikeys.tsv](http://stitch.embl.de/download/chemicals.inchikeys.v5.0.tsv.gz), [chemicals.tsv](http://stitch.embl.de/download/chemicals.v5.0.tsv.gz), [chemical_chemical_interactions.tsv](http://stitch.embl.de/download/chemical_chemical.links.detailed.v5.0.tsv.gz), [protein_chemical_interactions.tsv](http://stitch.embl.de/download/protein_chemical.links.transfer.v5.0.tsv.gz), and [actions.tsv](http://stitch.embl.de/download/actions.v5.0.tsv.gz) were downloaded, cleaned, and ingested. Other files include data downloaded from UniProt and Ensembl to map protein names: [uniprot_mapped_ids.dat](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz), [uniprot_archived_ids.txt](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/docs/sec_ac.txt), [archived_ensembls.txt](http://www.ensembl.org/biomart/martservice?query=%3C?xml%20version=%221.0%22%20encoding=%22UTF-8%22?%3E%20%3C!DOCTYPE%20Query%3E%3CQuery%20%20virtualSchemaName%20=%20%22default%22%20formatter%20=%20%22TSV%22%20header%20=%20%220%22%20uniqueRows%20=%20%220%22%20count%20=%20%22%22%20datasetConfigVersion%20=%20%220.6%22%20%3E%3CDataset%20name%20=%20%22hsapiens_gene_ensembl%22%20interface%20=%20%22default%22%20%3E%3CAttribute%20name%20=%20%22ensembl_peptide_id%22%20/%3E%3CAttribute%20name%20=%20%22uniprotswissprot%22%20/%3E%3CAttribute%20name%20=%20%22uniprotsptrembl%22%20/%3E%3C/Dataset%3E%3C/Query%3E). The current versions of the files can also be downloaded and processed by running [`download.sh`](download.sh).

### Overview

This directory stores the scripts used to download, clean, and convert the STITCH datasets into four CSV files. The files being `drugs.csv`, `drug_interactions.csv`, `protein_drug_interactions.csv`, and `actions.csv`. There is also a mapping file, `mapping_protein_names.csv`, created from UniProt and Ensembl data to map Ensembl IDs to the protein name. This file was needed to create the `protein_drug_interactions.csv` and `actions.csv`.

### Notes and Caveats

All three datasets have stereo compound IDs (CID) and flat CIDs, which is what we used to merge them. 

`chemical.sources.v5.0.tsv`
This file contained different source codes for various chemicals including: ChEMBL, ChEBI, ATC, BindingDB, KEGG, PS (PubChem Substance ID), and PC (PubChem Compound ID). 

`chemicals.inchikeys.v5.0.tsv`
There were some mismatched compound stereo IDs and compound flat IDs included in the inchikeys.tsv file, so these rows from the dataset were excluded. 

`chemicals.v5.0.tsv.gz`
This file contained chemical name, molecular weight, and SMILES string. Some of the longer chemical names are truncated. 

After merging the datasets, we added two columns for the corresponding MeSHDescriptor DCIDs and ChEMBL DCIDs through querying the Biomedical Data Commons. We also added a new DCID that is based on the PubChem Compound ID formatted as 'chem/CID#'. The text columns have been formatted to have double quotes.  

We found that sometimes there was more than 1 ChEMBL ID per STITCH ID. To account for this, we queried Data Commons for the ChEMBL ID using the InChIKey from STITCH. We included a 'same_as' column to indicate the ChEMBL ID found in Data Commons according to the matching InChIKey from STITCH. The value in that column is left blank if the InChIkey in that corresponding row does not match any InChIKey found in Data Commons.

We also found that there was multiple PubChem Substance and Compound IDs per STITCH ID. A lot of these IDs were similar, but not exact matches to the chemical compound in a given row. We decided to consider the "PS" and "PC" columns to be the PubChem IDs of similar substances and compounds. Because of this, we removed the PubChem Compound ID values that were an exact match to the STITCH ID of the particular chemical on a given row.

`chemical_chemical.links.detailed.v5.0.tsv`
This file contained informtion about drug-drug interactions and various scores. 

`protein_chemical.links.transfer.v5.0.tsv`
This file contained informtion about protein-drug interactions and various scores. 

`actions.v5.0.tsv`
This file contained informtion about protein-drug interactions and what the effects of these interactions were.

`uniprot_mapped_ids.dat`
This file contains information about the different IDs included in the UniProt database.

`uniprot_archived_ids.txt`
This file contains  the archived UniProt accession IDs that are no longer included the UniProt database and their respective updated accession ID.

`archived_ensembls.txt`
This file contains the archived Ensembl Protein IDs that are no longer included the Ensembl database. 

STITCH identified proteins through their STRING ID (which is derived from the Ensembl Protein ID), but a number of these IDs were deprecated and no longer maintained in the last few versions of Ensembl. This means that we were unable to map a few hundred out of 15 million protein Ensembl IDs back to its UniProt name. 

This import has large data storage and compute requirements to execute. This includes 25 GB for storing the original files.

### License

All data downloaded for this import belongs to STITCH. Any works found on the STITCH website may be licensed — both for commercial and for academic institutions. More information about the license can be found [here](http://stitch.embl.de/cgi/access.pl?UserId=f68rPwGhmUhl&sessionId=URI01tKFfMAQ&footer_active_subpage=licensing).

# About the Import

## Artifacts

### Scripts

#### Shell Scripts
[`download.sh`](download.sh) downloads the 9 datasets (6 from STITCH, 2 from UniProt, and 1 coming from Ensembl) and prepares it for data cleaning and processing.

#### Python Scripts
[`compile_stitch.py`](compile_stitch.py) cleans and merges three STITCH datasets (sources.tsv, inchikeys.tsv, and chemicals.tsv) into one CSV.

[`drug_interactions.py`](drug_interactions.py) cleans and creates PubChem DCIDs for drug interactions

[`protein_drug_interactions.py`](protein_drug_interactions.py) cleans, maps protein Ensembl IDs to the protein name, and creates PubChem DCIDs for protein-drug interactions 

[`actions.py`](actions.py) cleans, maps protein Ensembl IDs to the protein name, and creates PubChem DCIDs for protein-drug interactions 

[`create_mapping_file.py`](create_mapping_file.py) cleans, maps protein Ensembl IDs to the protein name, and creates PubChem DCIDs for protein-drug interactions 


#### Test Scripts
[`test_compile_stitch.py`](test_stitch.py) tests compile_stitch.py, drug_interactions.py, create_mapping_file.py, protein_drug_interactions.py, and  protein_actions.py scripts.


### Files

#### Test Files
[`sources_test.tsv`](test-data/sources_test.tsv) subsetted the sources.tsv file to only include PubChem Compound IDs 1-20

[`inchikeys_test.tsv`](test-data/inchikeys_test.tsv) subsetted the inchikeys.tsv file to only include PubChem Compound IDs 1-20

[`chemicals_test.tsv`](test-data/chemicals_test.tsv) subsetted the chemicals.tsv file to only include PubChem Compound IDs 1-20

[`drug_interactions_test.tsv`](test-data/drug_interactions_test.tsv) subsetted the chemical_chemical_interactions.tsv file to include 10 drug-drug interactions

[`protein_drug_interactions_test.tsv`](test-data/protein_drug_interactions_test.tsv) subsetted the protein_chemical_interactions.tsv file to include 10 protein-drug interactions

[`actions_test.tsv`](test-data/actions_test.tsv) subsetted the actions.tsv file to include 10 protein-drug interactions

[`uniprot_id_mapping_test.csv`](test-data/uniprot_id_mapping_test.csv) subsetted only the UniProt names needed for the [`actions_test.tsv`](test-data/actions_test.tsv) and [`protein_drug_interactions_test.tsv`](test-data/protein_drug_interactions_test.tsv)

[`archived_uniprot_test.csv`](test-data/archived_uniprot_test.csv) subsetted only the UniProt archived accession IDs needed for the [`actions_test.tsv`](test-data/actions_test.tsv) and [`protein_drug_interactions_test.tsv`](test-data/protein_drug_interactions_test.tsv)

[`archived_ensembls_test.csv`](test-data/archived_ensembls_test.csv) subsetted only the Ensembl Protein IDs contained in [`actions_test.tsv`](test-data/actions_test.tsv) and [`protein_drug_interactions_test.tsv`](test-data/protein_drug_interactions_test.tsv)


## Schema
The schema for the data sources for the drug information, drug interactions, and the mapping file to get protein names were generated without any scripts. 

### tMCF Files
[`drugs.tmcf`](tmcf/drugs.tmcf)

[`mapping_protein_names.tmcf`](tmcf/mapping_protein_names.tmcf)

[`drug_interactions.tmcf`](tmcf/drug_interactions.tmcf)

[`protein_drug_interactions.tmcf`](tmcf/protein_drug_interactions.tmcf)

[`actions.tmcf`](tmcf/actions.tmcf)

### Output Schema MCF Files

[`drugs.mcf`](https://github.com/mariam16548/schema/blob/main/biomedical_schema/drugs.mcf)

[`mapping_protein_names.mcf`](https://github.com/mariam16548/schema/blob/main/biomedical_schema/mapping_protein_names.mcf)

[`drug_interactions.mcf`](https://github.com/mariam16548/schema/blob/main/biomedical_schema/drug_interactions.mcf)

[`protein_drug_interactions.mcf`](https://github.com/mariam16548/schema/blob/main/biomedical_schema/protein_drug_interactions.mcf)

[`actions.mcf`](https://github.com/mariam16548/schema/blob/main/biomedical_schema/actions.mcf)

[`actions_enum.mcf`](https://github.com/mariam16548/schema/blob/main/biomedical_schema/actions_enum.mcf)


## Examples

### Run Tests

1. To test [`compile_stitch.py`](compile_stitch.py), [`create_mapping_file.py`](create_mapping_file.py), [`drug_interactions.py`](drug_interactions.py), [`protein_drug_interactions.py`](protein_drug_interactions.py), [`actions.py`](actions.py) run:

```
python test_stitch.py
```


### Import

1. Download the data to `scratch/`.

```
bash download.sh
```

2. Run the script to clean and merge the three datasets into `drugs.csv`. 

```
python compile_stitch.py 
  scratch/sources_sorted.tsv 
  scratch/inchikeys_sorted.tsv
  scratch/chemicals_no_header.tsv
```

3. Run the script to clean and format drug-drug interactions data and output `drug_interactions.csv`.
  
```
python drug_interactions.py 
  scratch/chemical_chemical_interactions.tsv
```

4. Run the script to clean and merge UniProt and Ensembl data and output `mapping_protein_names.csv`.
```
python create_mapping_file.py 
  scratch/archived_emsembls.txt
  scratch/uniprot_mapped_ids.dat
  scratch/uniprot_archived_ids.txt
```

5. Run the script to clean and map protein names in the protein-drug interactions data and output `protein_drug_interactions.csv`.
```
python protein_drug_interactions.py 
  scratch/protein_chemical_interactions.tsv
  scratch/mapping_protein_names.csv
```

6. Run the script to clean and map protein names in the protein-drug interactions data and output `protein_actions.csv`.
```
python actions.py 
  scratch/actions.tsv
  scratch/mapping_protein_names.csv
```
