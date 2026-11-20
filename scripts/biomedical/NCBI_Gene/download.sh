# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash

mkdir -p input; cd input

# download Gene Info data from NCBI Gene
curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz
gunzip gene_info.gz 
mv gene_info gene_info.txt


# download additional info on genes
curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene2pubmed.gz
gunzip gene2pubmed.gz
mv gene2pubmed gene2pubmed.txt

curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene_neighbors.gz
gunzip gene_neighbors.gz 
mv gene_neighbors gene_neighbors.txt


# download gene relationships
curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene_orthologs.gz
gunzip gene_orthologs.gz 
mv gene_orthologs gene_orthologs.txt

curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene_group.gz
gunzip gene_group.gz 
mv gene_group gene_group.txt


# download gene omim relationships
curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/mim2gene_medgen 
mv mim2gene_medgen mim2gene_medgen.txt


# download gene gene ontology relationships
curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene2go.gz
gunzip gene2go.gz
mv gene2go gene2go.txt


# download RNA transcript info
curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene2accession.gz
gunzip gene2accession.gz 
mv gene2accession gene2accession.txt

curl -L -O https://ftp.ncbi.nih.gov/gene/DATA/gene2ensembl.gz
gunzip gene2ensembl.gz 
mv gene2ensembl gene2ensembl.txt


# download gene function pubmed reference info
curl -L -O https://ftp.ncbi.nih.gov/gene/GeneRIF/generifs_basic.gz
gunzip generifs_basic.gz
mv generifs_basic generifs_basic.txt