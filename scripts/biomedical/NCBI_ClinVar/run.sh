#!/bin/bash

mkdir -p output;

# generate Genetic Variant mcfs using hg38 files & hg19 positions only mcfs
# make sure to keep the keep the below mwntioned four input files in 'input' folder  
# For HG19: hg19_clinvar.vcf & hg19_clinvar_papu.vcf
# For HG38: hg38_clinvar.vcf & hg38_clinvar_papu.vcf


python3 scripts/format_clinvar_and_position.py
