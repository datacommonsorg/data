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
"""
Author: Samantha Piekos
Date: 07/09/2024
Name: tests
Description: This file runs the Data Commons Java tool to run standard
tests on tmcf + CSV pairs for the NIH NLM MeSH import. This assumes that
the user has Java Remote Environment (JRE) installed, which is needed to
locally install Data Commons test tool (v. 0.1-alpha.1k) prior to calling
the tool to evaluate tmcf + CSV pairs.
"""

#!/bin/bash

# download data commons java test tool version 0.1-alpha.1k
mkdir -p tmp; cd tmp
wget https://github.com/datacommonsorg/import/releases/download/0.1-alpha.1k/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar *.mcf
cd ..


# initiate additional report directories
mkdir -p pharmGKB_primary_data_reports
mkdir -p pharmGKB_relationship_data_reports


# run tests on primary data file csv + tmcf pairs
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/chemicals.tmcf CSVs/chemicals.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/chemicals

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/drugs.tmcf CSVs/drugs.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/drugs

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/genes.tmcf CSVs/genes.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/genes

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/phenotypes.tmcf CSVs/phenotypes.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/phenotypes

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/phenotypes_mesh_supplementary_concept_record.tmcf CSVs/phenotypes_mesh_supplementary_concept_record.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/phenotypes_mesh_supplementary_concept_record

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/phenotypes_mesh_qualifier.tmcf CSVs/phenotypes_mesh_qualifier.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/phenotypes_mesh_qualifier

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/variants.tmcf CSVs/variants.csv *.mcf
mv dc_generated pharmGKB_primary_data_reports/variants


# run tests on relationship data file csv + tmcf pairs
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/chem_chem.tmcf CSVs/chem_chem.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/chem_chem

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/chem_gene.tmcf CSVs/chem_gene.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/chem_gene

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/chem_var.tmcf CSVs/chem_var.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/chem_var

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/disease_disease.tmcf CSVs/disease_disease.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/disease_disease

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/disease_gene.tmcf CSVs/disease_gene.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/disease_gene

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/disease_var.tmcf CSVs/disease_var.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/disease_var

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/gene_gene.tmcf CSVs/gene_gene.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/gene_gene

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/gene_var.tmcf CSVs/gene_var.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/gene_var

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/var_var.tmcf CSVs/var_var.csv *.mcf
mv dc_generated pharmGKB_relationship_data_reports/var_var
