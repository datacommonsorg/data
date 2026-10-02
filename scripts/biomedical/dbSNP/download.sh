'''
This file downloads the most recent version of the NCBI dbSNP
hg19 and hg38 data and prepares it for processing.
'''
#!/bin/bash

# make working directory
mkdir -p scratch; cd scratch

# download NCBI data
curl -o GCF_000001405.25.gz https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz
curl -o GCF_000001405.39.gz https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz

# unzip data and remove headers
gunzip -r GCF_000001405.25.gz
tail -n +39 GCF_000001405.25 > hg19_GCF_no_header.vcf
rm GCF_000001405.25
gunzip -r GCF_000001405.39.gz
tail -n +39 $GCF_000001405.39 > hg38_GCF_no_header.vcf
rm GCF_000001405.39

# identify and remove conflicting lines from file by duplicate rsIDs with different major or minor alleles reported                                                               
awk '!seen[$3,$4,$5]++' hg38_GCF_no_header.vcf | awk 'n=x[$3]{print n"\n"$0;} {x[$3]=$0;}' >  hg38_GCF_conflicting_entries.vcf
grep -v -x -f hg38_GCF_conflicting_entries.vcf hg38_GCF_no_header.vcf > hg38_GCF_no_conflicting_entries.vcf
