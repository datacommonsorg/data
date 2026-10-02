#!/bin/bash

mkdir -p input; cd input

# download ClinVar VCF files
curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
gunzip clinvar.vcf.gz
mv clinvar.vcf hg38_clinvar.vcf

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar_papu.vcf.gz
gunzip clinvar_papu.vcf.gz
mv clinvar_papu.vcf hg38_clinvar_papu.vcf

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar.vcf.gz
gunzip clinvar.vcf.gz
mv clinvar.vcf hg19_clinvar.vcf

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar_papu.vcf.gz
gunzip clinvar_papu.vcf.gz
mv clinvar_papu.vcf hg19_clinvar_papu.vcf
