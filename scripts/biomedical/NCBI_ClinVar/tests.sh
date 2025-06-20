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
# Date: 27/08/2024
# Name: tests
# Description: This file runs the Data Commons Java tool to run standard
# tests on tmcf + CSV pairs for the ClinVar data import.
# """

#!/bin/bash

# download data commons java test tool version 0.1-alpha.1k
rm -rf tmp
mkdir -p tmp; cd tmp
wget https://github.com/datacommonsorg/import/releases/download/0.1-alpha.1k/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar
cd ..
mkdir -p lint

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/clinvar.tmcf output/clinvar.csv
mv dc_generated lint/clinvar

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/clinvar_obs.tmcf output/clinvar_obs.csv
mv dc_generated lint/clinvar_obs

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/clinvar_conflicting.tmcf output/clinvar_conflicting.csv
mv dc_generated lint/clinvar_conflicting

java -jar tmp/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar genmcf tMCFs/clinvar_pos_only.tmcf output/clinvar_pos_only.csv
mv dc_generated lint/clinvar_pos_only
