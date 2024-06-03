#!/bin/bash

mkdir -p scripts/input; cd scripts/input

# download assembly summary files.
curl -o assembly_summary_genbank.txt https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt
curl -o assembly_summary_refseq.txt https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt