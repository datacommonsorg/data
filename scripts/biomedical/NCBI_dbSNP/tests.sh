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

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/GRCh37.tmcf output/ncbi_GRCh37_genome_assembly_report.csv -n 20 -o lint/GRCh37

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/GRCh38.tmcf output/ncbi_GRCh38_genome_assembly_report.csv -n 20 -o lint/GRCh38

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/MedGen.tmcf output/medgen.csv -n 20 -o lint/medgen

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/clinvar_diesease_gene.tmcf output/clinvar_diesease_gene.csv -n 20 -o lint/clinvar_diesease_gene

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/hg19_positions.tmcf output/GCF25/*.csv -n 20 -o lint/GCF25

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/dbsnp_freq.tmcf output/freq/*.csv -n 20 -o lint/freq

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/dbsnp_hg38.tmcf output/GCF40/hg38/*.csv -n 20 -o lint/GCF40/hg38

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/dbsnp_hg38_alleles.tmcf output/GCF40/hg38alleles/*.csv -n 20 -o lint/GCF40/hg38alleles

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/dbsnp_hg38_allele_disease_associations.tmcf output/GCF40/hg38alleledisease/*.csv -n 20 -o lint/GCF40/hg38alleledisease

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/dbsnp_hg38_alllele_drug_response_associations.tmcf output/GCF40/hg38alleledrug/*.csv -n 20 -o lint/GCF40/hg38alleledrug

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/dbsnp_hg38_freq.tmcf output/GCF40/hg38freq/*.csv -n 20 -o lint/GCF40/hg38freq


