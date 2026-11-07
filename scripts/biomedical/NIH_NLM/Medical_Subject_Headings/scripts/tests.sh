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
Date: 03/11/2024
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
wget https://github.com/datacommonsorg/import/releases/download/0.1-alpha.1k/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar
cd ..

# run tests on desc file csv + tmcf pairs
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_concept.tmcf CSVs/mesh_desc_concept.csv
mv dc_generated mesh_desc_concept

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_concept_mapping.tmcf CSVs/mesh_desc_concept_mapping.csv
mv dc_generated mesh_desc_concept_mapping

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_descriptor.tmcf CSVs/mesh_desc_descriptor.csv
mv dc_generated mesh_desc_descriptor

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_descriptor_mapping.tmcf CSVs/mesh_desc_descriptor_mapping.csv
mv dc_generated mesh_desc_descriptor_mapping

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_qualifier.tmcf CSVs/mesh_desc_qualifier.csv
mv dc_generated mesh_desc_qualifier

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_qualifier_mapping.tmcf CSVs/mesh_desc_qualifier_mapping.csv
mv dc_generated mesh_desc_qualifier_mapping

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_term.tmcf CSVs/mesh_desc_term.csv
mv dc_generated mesh_desc_term

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_desc_term_mapping.tmcf CSVs/mesh_desc_term_mapping.csv
mv dc_generated mesh_desc_term_mapping


# run tests on pa file csv + tmcf pairs
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_pharmacological_action_descriptor.tmcf CSVs/mesh_pharmacological_action_descriptor.csv
mv dc_generated mesh_pharmacological_action_descriptor

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_pharmacological_action_record.tmcf CSVs/mesh_pharmacological_action_record.csv
mv dc_generated mesh_pharmacological_action_record


# run tests on qual file csv + tmcf pairs
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_qual_concept.tmcf CSVs/mesh_qual_concept.csv
mv dc_generated mesh_qual_concept

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_qual_concept_mapping.tmcf CSVs/mesh_qual_concept_mapping.csv
mv dc_generated mesh_qual_concept_mapping

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_qual_qualifier.tmcf CSVs/mesh_qual_qualifier.csv
mv dc_generated mesh_qual_qualifier

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_qual_term.tmcf CSVs/mesh_qual_term.csv
mv dc_generated mesh_qual_term


# run tests on record and pubchem files csv + tmcf pairs
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_record.tmcf CSVs/mesh_record.csv
mv dc_generated mesh_record

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/mesh_pubchem_mapping.tmcf CSVs/mesh_pubchem_mapping.csv
mv dc_generated mesh_pubchem_mapping
