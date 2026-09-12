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
    - [Schema Generation](#schema-generation)  

# About the Dataset
[dbSNP](https://www.ncbi.nlm.nih.gov/snp/?cmd=search) is an NCBI public-domain database of a broad array of simple genetic variations. It "contains human single nucleotide variations, microsatellites, and small-scale insertions and deletions along with publication, population frequency, molecular consequence, and genomic and RefSeq mapping information for both common variations and clinical mutations." Any type of variation is accepted including "single-base nucleotide substitutions (also known as single nucleotide polymorphisms or SNPs), small-scale multi-base deletions or insertions (also called deletion insertion polymorphisms or DIPs), and retroposable element insertions and microsatellite repeat variations (also called short tandem repeats or STRs)." The database is updated semi-annually to include new submissions. 

dbSNP previously accepted, maintained, and supported genetic variants from any and all organisms, however, this ended in December 2018. Now, it only supports new submissions for genetic variants in humans. We have included all human genetic variants from dbSNP in Data Commons supporting both genome assemblies hg19 and hg38.

### Download Data
Data was downloaded as VCFs using the [FTP download](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/) functionality. Files for both [hg19](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz) and [hg38](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.38.gz) were downloaded, cleaned, and ingested. The current versions of the vcf files for both hg19 and hg38 assemblies can also be downloaded by running [`download.sh`](download.sh).

In addition, to create the key to convert chromosome RefSeq IDs to the corresponding Chromosome dcids in the Biomedical Data Commons graph, data from [NCBI Assembly](https://www.ncbi.nlm.nih.gov/assembly) for [hg19](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.13_GRCh37/GCF_000001405.13_GRCh37_assembly_report.txt) and [hg38](https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.26) as well as the most recent patches released for both [hg19](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.25_GRCh37.p13/GCF_000001405.25_GRCh37.p13_assembly_report.txt) and [hg38](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.40_GRCh38.p14/GCF_000001405.40_GRCh38.p14_assembly_report.txt). Downloading and processing of the data to generate the mapping key as a text file is all accomplished by [`make_refseq_chromosome_to_dcid_key.sh`](make_refseq_chromosome_to_dcid_key.sh).

### Overview

This directory stores the scripts used to download, clean, and convert the NCBI dbSNP data into MCF format. It also includes scripts used to automatically generate GeneticVariant property values for alternative IDs as well as the population studies for the

### Notes and Caveats

This import has large data storage and compute requirements to execute. This includes 360 GB for storing the original files, an additional 360 GB for intermediate files, and 2 TB for the output files. It also requires parallel processing with ~7,000 serial hours at 2 GB of RAM required to run all the code provided here to generate this import. This imports also details how to clean data from the two most recent human genome assemblies hg19 and hg38. The only data taken from the hg19 dbSNP file is the genomic position, whereas all information contained in the hg38 file is cleaned and written to MCF files. This was done because all information besides the genomic position, which is unique to the genome assembly is duplicated between the two files and therefore only needs to be imported from one of them. Prior to cleaning the dbSNP data and converting it to MCF format, a user must create a key to map chromosome RefSeq IDs to the corresponding Biomedical Data Commons Chromosome dcids. Finally, the schema for population studies measuring frequencies of genetic variant alleles and GeneticVariant properties representing alternative dcids need to be generated using scripts.

In addition, the data representation in the original import files is dense and uses mixed seperators making extraction difficult. Update frequency for dbSNP is roughly on an annual schedule, but commonly involves the addition of new properties, alternative database IDs, or population studies of allele frequencies. Furthermore, although effort was made to fix obvious data entry errors (e.g. a population study being recorded as "Stonian" in dbSNP instead of "Estonian") additional errors in data entry may still exist in the final import.

### License

All data downloaded for this import belongs to the U.S. National Library of Medicine (NLM). Any works found on NLM websites may be freely used or reproduced without permission in the U.S. More information about the license can be found [here](https://www.nlm.nih.gov/web_policies.html).

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

### Schema Generation

1. Generate schema mcf GenVarSourceEnum to reperesent all population studies that report measurements on one or more genetic variants in dbSNP

```
python format_dbSNP_GenVarSource_enum_schema.py 
  scratch/hg38_GCF_no_conflicting_entries.vcf 
  GeneticVariant_GenVarSource_enums.mcf
```

2. Generate schema mcf for initiating GeneticVariant property values for all alternative database IDs that are reported for one or more genetic variant in dbSNP

```
python format_dbSNP_alt_ID_database_property_schema.py 
  scratch/hg38_GCF_no_conflicting_entries.vcf 
  GeneticVariant_Alt_ID_Database_properties.mcf
```
