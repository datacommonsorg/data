#!/bin/bash

mkdir -p input; cd input

# download the newest ncbi taxdump file and uncompress it
curl -o ncbi_taxdump.tar.Z https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.Z
uncompress ncbi_taxdump.tar.Z
tar -xvf ncbi_taxdump.tar
rm ncbi_taxdump.tar

# download the newest ncbi taxcat file and uncompress it
curl -o ncbi_taxcat.tar.gz https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxcat.tar.gz
tar -xvzf ncbi_taxcat.tar.gz
rm ncbi_taxcat.tar.gz
