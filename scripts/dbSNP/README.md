# Database Overview
[dbSNP](https://www.ncbi.nlm.nih.gov/snp/?cmd=search) is an NCBI public-domain database of a broad array of simple genetic variations. It "contains human single nucleotide variations, microsatellites, and small-scale insertions and deletions along with publication, population frequency, molecular consequence, and genomic and RefSeq mapping information for both common variations and clinical mutations." Any type of variation is accepted including "single-base nucleotide substitutions (also known as single nucleotide polymorphisms or SNPs), small-scale multi-base deletions or insertions (also called deletion insertion polymorphisms or DIPs), and retroposable element insertions and microsatellite repeat variations (also called short tandem repeats or STRs)." The database is updated semi-annually to include new submissions. 

dbSNP previously accepted, maintained, and supported genetic variants from any and all organisms, however, this ended in December 2018. Now, it only supports new submissions for genetic variants in humans. We have included all human genetic variants from dbSNP in Data Commons supporting both genome assemblies hg19 and hg38.

## Database Download
Data was downloaded as VCFs using the [FTP download](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/) functionality. Files for both [hg19](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz) and [hg38](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.38.gz) were downloaded and parsed.

# Generation of MCFs

## scripts used
[format_dbSNP_GenVarSource_enum_schema.py](https://github.com/datacommonsorg/data/blob/spiekos-patch-1/scripts/dbSNP/format_dbSNP_GenVarSource_enum_schema.py)
[format_dbSNP_alt_ID_database_property_schema.py](https://github.com/datacommonsorg/data/blob/spiekos-patch-1/scripts/dbSNP/format_dbSNP_alt_ID_database_property_schema.py)


## Generation of schema by script
The schema for both the data sources for the allele frequencies of genetic variants and the databases with alternative IDs for genetic variants were generated using scripts. The GenVarSourceEnum for data sources of allele frequencies is generated using [format_dbSNP_GenVarSource_enum_schema.py](https://github.com/datacommonsorg/data/blob/spiekos-patch-1/scripts/dbSNP/format_dbSNP_GenVarSource_enum_schema.py). The GeneticVariant properties for alternative IDs is generated using [format_dbSNP_alt_ID_database_property_schema.py](https://github.com/datacommonsorg/data/blob/spiekos-patch-1/scripts/dbSNP/format_dbSNP_alt_ID_database_property_schema.py).
