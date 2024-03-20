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
Date: 03/05/2024
Name: tests
Description: This file runs the Data Commons Java tool to run standard
tests on tmcf + CSV pairs for the DISEASES by JensenLab import.
"""

#!/bin/bash

# download data commons java test tool version 0.1-alpha.1k
mkdir -p tmp; cd tmp
wget https://github.com/datacommonsorg/import/releases/download/0.1-alpha.1k/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar
cd ..

# run tests
java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/codingGenes-knowledge.tmcf CSVs/codingGenes-knowledge.csv
mv dc_generated codingGenes-knowledge

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/codingGenes-textmining.tmcf CSVs/codingGenes-textmining.csv
mv dc_generated codingGenes-textmining

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/experiment.tmcf CSVs/codingGenes-experiments.csv
mv dc_generated experiment

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/nonCodingGenes-knowledge.tmcf CSVs/nonCodingGenes-knowledge.csv
mv dc_generated nonCodingGenes-knowledge

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/nonCodingGenes-textmining.tmcf CSVs/nonCodingGenes-textmining.csv
mv dc_generated nonCodingGenes-textmining
