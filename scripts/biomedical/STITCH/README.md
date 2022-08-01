# Importing dbSNP data from NCBI

## Table of Contents

- [Importing Medical Subject Headings (MeSH) data from NCBI](#importing-medical-subject-headings-mesh-data-from-ncbi)
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
       - [Scripts](#scripts)
       - [Output Schema MCF Files](#output-schema-mcf-files)
  - [Examples](#examples)
    - [Run Tests](#run-testers)
    - [Import](#import)

# About the Dataset
[STITCH](http://stitch.embl.de/cgi/input.pl?UserId=f68rPwGhmUhl&sessionId=URI01tKFfMAQ) ('Search Tool for Interacting Chemicals') is a public-domain database of 430,000 chemicals. It contains "known and predicted interactions between chemicals and proteins. The interactions include direct (physical) and indirect (functional) associations; they stem from computational prediction, from knowledge transfer between organisms, and from interactions aggregated from other (primary) databases." The last time the database was updated was in 2016. 

### Download Data
Data was downloaded as TSVs from the [STITCH website](http://stitch.embl.de/cgi/download.pl). Files for [sources.tsv](http://stitch.embl.de/download/chemical.sources.v5.0.tsv.gz) and [inchikeys.tsv](http://stitch.embl.de/download/chemicals.inchikeys.v5.0.tsv.gz) and [chemicals.tsv](http://stitch.embl.de/download/chemicals.v5.0.tsv.gz) were downloaded, cleaned, and ingested. The current versions of the TSV files can also be downloaded and processed by running [`download.sh`](download.sh).

### Overview

This directory stores the scripts used to download, clean, and convert the STITCH datasets into one CSV file. 

### Notes and Caveats

All three datasets have stereo compound IDs (CID) and flat CIDs, which is what we used to merge them. 

chemical.sources.v5.0.tsv
This file contained different source codes for various chemicals including: ChEMBL, ChEBI, ATC, BindingDB, KEGG, PS (PubChem Substance IDs of similar compounds), and PC (PubChem Compound IDs of similar compounds). We removed the PC values that were an exact match to the CID of the particular chemical on a given row.

chemicals.inchikeys.v5.0.tsv 
There were some mismatched compound stereo IDs and compound flat IDs included in the inchikeys.tsv file, so these rows from the dataset were excluded. 
We created a same_as column in the final CSV of the Chemical Compound DCIDs in which the InChIkey in the dataset matches the InChIkey in Data Commons. The value in that column is left blank if the InChIkey in that corresponding row does not match any InChIkey found in Data Commons.

chemicals.v5.0.tsv.gz
This file contained chemical name, molecular weight, and SMILES string. Some of the longer chemical names are truncated. 

After merging the datasets, I added two columns for the corresponding MeSHDescriptor DCIDs and Chemical Compound DCIDs through querying the Biomedical Data Commons. I also formatted the text columns to have double quotes.  

This import has large data storage and compute requirements to execute. This includes 25 GB for storing the original files.


### License

All data downloaded for this import belongs to STITCH. Any works found on the STITCH website may be licensed — both for commercial and for academic institutions. More information about the license can be found [here](http://stitch.embl.de/cgi/access.pl?UserId=f68rPwGhmUhl&sessionId=URI01tKFfMAQ&footer_active_subpage=licensing).

# About the Import

## Artifacts

### Scripts

#### Shell Scripts
[`download.sh`](download.sh) downloads the dbSNP data for hg19 and hg38 and prepares it for data cleaning and processing.

[`make_refseq_chromosome_to_dcid_key.sh`](make_refseq_chromosome_to_dcid_key.sh) downloads NCBI Assembly data for the most recent releases of the hg19 and hg38 assemblies and uses this data to create a mapping key of chromosome RefSeq ID to dcid, which it outputs as a text file.

[`split.sh`](split.sh) splits the dbSNP input file into several hundred files of 1,250,000 lines each to enable parallel processing of the data cleaning and reformatting step.

#### Python Scripts

[`format_refseq_chromosome_id_to_dcid.py`](format_refseq_chromosome_id_to_dcid.py) generates mapping key of chromosome RefSeq ID to corresponding dcid.

[`format_dbsnp.py`](format_dbsnp.py) cleans and converts all dbSNP data to MCF format.

[`format_dbsnp_pos_only.py`](format_dbsnp_pos_only.py) cleans and converts genomic position only for dbSNP genetic variant data to MCF format.

#### Test Scripts

### Files

#### Test Files

## Schema
The schema for both the data sources for the allele frequencies of genetic variants and the databases with alternative IDs for genetic variants were generated using scripts. The GenVarSourceEnum for data sources of allele frequencies is generated using [format_dbSNP_GenVarSource_enum_schema.py](schema/format_dbSNP_GenVarSource_enum_schema.py). The GeneticVariant properties for alternative IDs is generated using [format_dbSNP_alt_ID_database_property_schema.py](schema/format_dbSNP_alt_ID_database_property_schema.py).

### Scripts
[`format_dbSNP_GenVarSource_enum_schema.py`](schema/format_dbSNP_GenVarSource_enum_schema.py) generates the schema ([GenVarSourceEnum](https://datacommons.org/browser/GenVarSourceEnum)) used to represent the population study in which allele frequencies of genetic variants were observed.

[`format_dbSNP_alt_ID_database_property_schema.py`](schema/format_dbSNP_alt_ID_database_property_schema.py) generates [GeneticVariant](https://datacommons.org/browser/GeneticVariant) property values for each alternative database ID associated with one or more genetic variants reported in dbSNP.

### Output Schema MCF Files

[`GeneticVariant_GenVarSource_enums.mcf`](schema/GeneticVariant_GenVarSource_enums.mcf)

[`GeneticVariant_Alt_ID_Database_properties.mcf`](schema/GeneticVariant_Alt_ID_Database_properties.mcf)

## Examples

### Run Tests

1. To test [`format_refseq_chromosome_id_to_dcid.py`](format_refseq_chromosome_id_to_dcid.py) run:

```
python test_chromosome_key_script.py
```

2. To test [`format_dbsnp.py`](format_dbsnp.py) run:

```
python test_format_dbsnp.py
```

3. To test [`format_dbsnp_pos_only.py`](format_dbsnp_pos_only.py) run:

```
python test_format_dbsnp_pos_only.py
```

4. To test [`format_dbSNP_GenVarSource_enum_schema.py`](schema/format_dbSNP_GenVarSource_enum_schema.py) run:

```
python test_GenVarSourceEnum_schema_creation.py
```

6. To test [`format_dbSNP_alt_ID_database_property_schema.py`](schema/format_dbSNP_alt_ID_database_property_schema.py) run:

```
python test_alt_database_ID_schema_creation.py
```

### Import

1. Download the data to `scratch/`.

```
bash download.sh
```

2. Generate the text file that maps Chromosome RefSeq IDs used in dbSNP to corresponding Chromosome dcids in the Data Commons knowledge graph.

```
bash make_refseq_chromosome_to_dcid_key.sh
```

3. Split the input files (1,250,000 lines per file) for parallel processing during the data cleaning step.

```
bash split.sh
```

4. Parallely run the script to clean and convert hg38 data to an output MCF, which is needed for import into the graph. This script takes records information about the genetic variant in the output MCF.

```
python format_dbsnp.py 
  scratch/hg38_subset/hg38_GCF_subset_*.vcf 
  output/hg38/hg38_subset_output_*.mcf 
  hg38
```

5. Parallely run the script to clean and convert hg19 data to an output MCF, which is needed for import into the graph. This script only records information about the hg19 genomic position of the genetic variant in the output MCF.

```
python format_dbsnp_pos_only.py 
  scratch/hg19_subset/hg19_GCF_subset_*.vcf 
  output/hg19/hg19_subset_output_*.mcf 
  hg19
```