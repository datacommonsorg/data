#!/bin/bash

mkdir -p input; cd input

# download genome assemblies files
curl -L -O https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.14_GRCh37.p13/GCA_000001405.14_GRCh37.p13_assembly_report.txt

curl -L -O https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_report.txt

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/medgen/NAMES.RRF.gz
gunzip NAMES.RRF.gz
mv NAMES.RRF NAMES.txt

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/medgen/MGDEF.RRF.gz
gunzip MGDEF.RRF.gz
mv MGDEF.RRF MGDEF.txt

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/medgen/MGSTY.RRF.gz
gunzip MGSTY.RRF.gz
mv MGSTY.RRF MGSTY.txt

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGenIDMappings.txt.gz
gunzip MedGenIDMappings.txt.gz

curl -L -O https://ftp.ncbi.nlm.nih.gov/pub/clinvar/gene_condition_source_id
gunzip gene_condition_source_id
mv gene_condition_source_id gene_condition_source_id.txt

mkdir -p GCF25; cd GCF25

curl -L -O https://ftp.ncbi.nlm.nih.gov/snp/latest_release/VCF/GCF_000001405.25.gz
gunzip GCF_000001405.25.gz
mv GCF_000001405.25 GCF_000001405.25.vcf

cd ..
mkdir -p GCF40; cd GCF40

curl -L -O https://ftp.ncbi.nlm.nih.gov/snp/latest_release/VCF/GCF_000001405.40.gz
gunzip GCF_000001405.40.gz
mv GCF_000001405.40 GCF_000001405.40.vcf

cd ..
mkdir -p freq; cd freq

curl -L -O https://ftp.ncbi.nlm.nih.gov/snp/population_frequency/latest_release/freq.vcf.gz
gunzip freq.vcf.gz
cd ..
