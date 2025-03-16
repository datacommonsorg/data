'''
This file downloads the hg19 and hg38 NCBI Assemblies as well as their
most recent patches. It then uses this data to make a key for mapping
the chromosome refseq ID to the corresponding dcid to be used as part
of the data cleaning import converting NCBI dbSNP to MCF format.
'''
#!/bin/bash

# navigate to the scratch folder
cd scratch

# download NCBI assembly files
curl -o GCF_000001405.13_GRCh37_assembly_report.txt https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.13_GRCh37/GCF_000001405.13_GRCh37_assembly_report.txt
curl -o GCF_000001405.25_GRCh37.p13_assembly_report.txt https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.25_GRCh37.p13/GCF_000001405.25_GRCh37.p13_assembly_report.txt
curl -o GCF_000001405.13_GRCh38_assembly_report.txt https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.26_GRCh38/GCF_000001405.26_GRCh38_assembly_report.txt
curl -o GCF_000001405.40_GRCh38.p14_assembly_report.txt https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.40_GRCh38.p14/GCF_000001405.40_GRCh38.p14_assembly_report.txt

# remove headers
tail -n +36 GCF_000001405.13_GRCh37_assembly_report.txt > refseq_id_hg19_chromosomes.txt
rm GCF_000001405.13_GRCh37_assembly_report.txt
tail -n +38 GCF_000001405.25_GRCh37.p13_assembly_report.txt > refseq_id_hg19_patch13_chromosomes.txt
rm GCF_000001405.25_GRCh37.p13_assembly_report.txt
tail -n +63 GCF_000001405.13_GRCh38_assembly_report.txt  > refseq_id_hg38_chromosomes.txt
rm GCF_000001405.13_GRCh38_assembly_report.txt
tail -n +65 GCF_000001405.40_GRCh38.p14_assembly_report.txt > refseq_id_hg38_patch14_chromosomes.txt
rm GCF_000001405.40_GRCh38.p14_assembly_report.txt

# run python script to make chromosome refseq ID to dcid key
python3 ../format_refseq_chromosome_id_to_dcid.py refseq_id_hg19_chromosomes.txt refseq_id_hg19_patch13_chromosomes.txt refseq_id_hg38_chromosomes.txt refseq_id_hg38_patch14_chromosomes.txt ../refseq_id_chromosome_dcid.txt
rm refseq_id*
