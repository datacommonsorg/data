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
Date: 02/26/2024
Name: tests
Description: This file runs the Data Commons Java tool to run standard
tests on tmcf + CSV pairs for the DISEASES by JensenLab import.
"""

#!/bin/bash

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/codingGenes-manual.tmcf CSVs/codingGenes-manual.csv
mv dc_generated codingGenes-manual

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/codingGenes-textMining.tmcf CSVs/codingGenes-textMining.csv
mv dc_generated codingGenes-textMining

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/experiment.tmcf CSVs/experiment.csv
mv dc_generated experiment

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/nonCodingGenes-manual.tmcf CSVs/nonCodingGenes-manual.csv
mv dc_generated nonCodingGenes-manual

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/nonCodingGenes-textMining.tmcf CSVs/nonCodingGenes-textMining.csv
mv dc_generated nonCodingGenes-textMining
