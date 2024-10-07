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


# """
# Author: Pradeep Kumar Krishnaswamy
# Date: 23/08/2024
# Name: tests
# Description: This file runs the Data Commons Java tool to run standard
# tests on tmcf + CSV pairs for the NCBI Gene data import.
# """

#!/bin/bash

# download data commons java test tool version 0.1-alpha.1k
rm -rf tmp
mkdir -p tmp; cd tmp
wget https://github.com/datacommonsorg/import/releases/download/0.1-alpha.1k/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar
cd ..
mkdir -p lint

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_gene.tmcf  output/gene_info/gene_info*.csv  output/ncbi_gene_schema_enum.mcf -n 20 -o lint/ncbi_gene_gene

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_gene_db.tmcf  output/ncbi_gene_gene_db.csv -n 20 -o lint/ncbi_gene_gene_db

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_pubmed.tmcf  output/ncbi_gene_gene_pubmed.csv -n 20 -o lint/ncbi_gene_gene_pubmed

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_ortholog.tmcf  output/ncbi_gene_gene_ortholog.csv -n 20 -o lint/ncbi_gene_gene_ortholog

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_phenotype_associations.tmcf  output/ncbi_gene_gene_phenotype_association.csv -n 20 -o lint/ncbi_gene_gene_phenotype_association

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_gene_group.tmcf  output/ncbi_gene_gene_group.csv -n 20 -o lint/ncbi_gene_gene_group

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_ensembl.tmcf  output/ncbi_gene_ensembl.csv -n 20 -o lint/ncbi_gene_ensembl

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_gene_rif.tmcf  output/ncbi_gene_gene_rif.csv -n 20 -o lint/ncbi_gene_gene_rif

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_genomic_coordinates.tmcf  output/gene_neighbors/gene_neighbors*.csv -n 20 -o lint/ncbi_gene_genomic_coordinates

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_go_terms.tmcf  output/gene2go/gene2go*.csv -n 20 -o lint/ncbi_gene_go_terms

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/ncbi_gene_rna_transcript.tmcf  output/gene2accession/gene2accession*.csv -n 20 -o lint/ncbi_gene_rna_transcript
