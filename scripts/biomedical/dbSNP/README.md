# Importing dbSNP data from NCBI

## Table of Contents

- [Importing Medical Subject Headings (MeSH) data from NCBI](#importing-medical-subject-headings-mesh-data-from-ncbi)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [tMCFs](#tmcfs)
     - [Schema](#schema)
  - [Examples](#examples)

# About the Dataset
[dbSNP](https://www.ncbi.nlm.nih.gov/snp/?cmd=search) is an NCBI public-domain database of a broad array of simple genetic variations. It "contains human single nucleotide variations, microsatellites, and small-scale insertions and deletions along with publication, population frequency, molecular consequence, and genomic and RefSeq mapping information for both common variations and clinical mutations." Any type of variation is accepted including "single-base nucleotide substitutions (also known as single nucleotide polymorphisms or SNPs), small-scale multi-base deletions or insertions (also called deletion insertion polymorphisms or DIPs), and retroposable element insertions and microsatellite repeat variations (also called short tandem repeats or STRs)." The database is updated semi-annually to include new submissions. 

dbSNP previously accepted, maintained, and supported genetic variants from any and all organisms, however, this ended in December 2018. Now, it only supports new submissions for genetic variants in humans. We have included all human genetic variants from dbSNP in Data Commons supporting both genome assemblies hg19 and hg38.

### Download URL
Data was downloaded as VCFs using the [FTP download](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/) functionality. Files for both [hg19](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz) and [hg38](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.38.gz) were downloaded, cleaned, and ingested. The current versions of the vcf files for both hg19 and hg38 assemblies can also be downloaded by running [`download.sh`](download.sh).

### Overview

This directory stores the scripts used to download, clean, and convert the NCBI dbSNP data into MCF format. It also includes scripts used to automatically generate GeneticVariant property values for alternative IDs as well as the population studies for the

### Notes and Caveats

This import has large data storage and compute requirements to execute. This includes 360 GB for storing the original files, an additional 360 GB for intermediate files and 2 TB for the output files. It also requires parallel processing with 

### License

Any works found on National Library of Medicine (NLM) Web sites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

# Generation of MCFs

## scripts used
[`format_dbSNP_GenVarSource_enum_schema.py`](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_GenVarSource_enum_schema.py)

[`format_dbSNP_alt_ID_database_property_schema.py`](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_alt_ID_database_property_schema.py)


## Generation of schema by script
The schema for both the data sources for the allele frequencies of genetic variants and the databases with alternative IDs for genetic variants were generated using scripts. The GenVarSourceEnum for data sources of allele frequencies is generated using [format_dbSNP_GenVarSource_enum_schema.py](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_GenVarSource_enum_schema.py). The GeneticVariant properties for alternative IDs is generated using [format_dbSNP_alt_ID_database_property_schema.py](https://github.com/datacommonsorg/data/blob/master/scripts/biomedical/dbSNP/format_dbSNP_alt_ID_database_property_schema.py).
