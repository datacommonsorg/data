# Importing NCBI Assembly Data

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Database Overview](#database-overview)
    3. [Schema Overview] (#schema-overi)
    4. [Notes and Caveats](#notes-and-caveats)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)


## About the Dataset

### Download URL

Assembly report data can be downloaded from the National Center for Biotechnology Information (NCBI) Assembly database using their [Genomes FTP Site] (https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/). Thus far the latest assembly versions for human genomes hg19 ([GRCh37] (https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.13_GRCh37/GCF_000001405.13_GRCh37_assembly_report.txt)) and hg38 ([GRCh38]  (https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.26_GRCh38/GCF_000001405.26_GRCh38_assembly_report.txt)) have been downloaded. The data is roughly in tab delimited format (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Database Overview

This directory stores the script used to import assembly report datasets from NCBI Assembly database. Assembly contains information on genome assemblies including their structure, collection of completely sequenced chromosomes, and unaligned sequence fragments More on the nature of the data contained in Assembly can be found on their [website] (https://www.ncbi.nlm.nih.gov/assembly/help/).

### Schema Overview

The schema representing data from NCBI assembly reports is represented in [GenomeAnnotation.mcf] (https://github.com/datacommonsorg/data/tree/master/schema/GenomeAnnotation.mcf) and [GenomeAnnotationEnum.mcf] (https://github.com/datacommonsorg/data/tree/master/schema/GenomeAnnotationEnum.mcf).

The assembly reports contains instances of entities "GenomeAssembly", "GenomeAssemblyUnit", and "Chromosome". All of these are connected to entity "Species" by property "ofSpecies". "GenomeAssemblyUnit" and "Chromosome" are connected to "GenomeAssembly" entities with property "inGenomeAssembly". "Chromosome" is connected to "GenomeAssemblyUnit" entities by property "inGenomeAssemblyUnit". Finally, genome sequences of type "Chromosome" that are unlocalized scaffolds link to associated "Chromosome" entity by property "inChromosome".

For a "GenomeAssembly" entity whether the assembly is a full genome representation or if RefSeq and GenBank assemblies are identical are represented as boolean values of the properties "isGenomeRepresentationFull" and "isRefSeqGenBankAssembliesIdentical" respectively. Properties representing "genomeAssemblyType", "genomeAssemblyReleaseType", "genomeAssemblyLevel", and "refSeqCategory" are represented by ennummerations "GenomeAssemblyTypeEunum", "GenomeAssemblyReleaseTypeEnum", "GenomeAssemblyLevelEnum", and "RefSeqCategoryEnum" respectively. "GenomeAssembly" has additional text value properties "ncbiTaxonID", "ncbiBioProject", "submitter", "date", "description", "ncbiAssemblyName", "genBankAssemblyAccession", and "refSeqAssemblyAccession".

For "GenomeAssemblyUnit" text value properties include "genBankAccession" and "refSeqAccession".

For "Chromosome" text value properties include "ncbiDNASequenceName", "genBankAccession", and "refSeqAccession". It also includes "Quantity" value "chromosomeSize" with unit "BasePairs". The property "dnaSequenceRole" property is represented by enummeration "dnaSequenceRoleEnum".

### Notes and Caveats

Assembly includes viral, prokaryotic, eukaryotic genomes including historical genome assemblies. However, here we only include a subset of the most recent versions of major genome assemblies. The raw data of additional genome assembly reports can be found in [this directory] (https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/).

### License

This data is from an NIH National Library of Medicine (NLM) genome unrestricted-access data repository and made accessible under the [NIH Genomic Data Sharing (GDS) Policy] (https://osp.od.nih.gov/scientific-sharing/genomic-data-sharing/) and the [NLM Accessibility policy] (https://www.nlm.nih.gov/accessibility.html). Additional information on "NCBI Website and Data Usage Policies" can be found [here] (https://www.ncbi.nlm.nih.gov/home/about/policies/).
