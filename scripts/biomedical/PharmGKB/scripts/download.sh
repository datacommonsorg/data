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
Date: 04/11/2024
Name: download
Description: This file downloads all files to be cleaned from PharmGKB,
saving them to a subdirectory named 'input'.
"""

#!/bin/bash

mkdir -p input; cd input

# download the Primary Data from pharmGKB
mkdir -p chemicals; cd chemicals
curl -L -O https://api.pharmgkb.org/v1/download/file/data/chemicals.zip
unzip chemicals.zip
rm chemicals.zip

cd ../; mkdir -p drugs; cd drugs
curl -L -O https://api.pharmgkb.org/v1/download/file/data/drugs.zip
unzip drugs.zip
rm drugs.zip

cd ../; mkdir -p genes; cd genes
curl -L -O https://api.pharmgkb.org/v1/download/file/data/genes.zip
unzip genes.zip
rm genes.zip

cd ../; mkdir -p phenotypes; cd phenotypes
curl -L -O https://api.pharmgkb.org/v1/download/file/data/phenotypes.zip
unzip phenotypes.zip
rm phenotypes.zip

cd ../; mkdir -p variants; cd variants
curl -L -O https://api.pharmgkb.org/v1/download/file/data/variants.zip
unzip variants.zip
rm variants.zip

# download Relationships Data from pharmGKB
cd ../; mkdir -p relationships; cd relationships
curl -L -O https://api.pharmgkb.org/v1/download/file/data/relationships.zip
unzip relationships.zip
rm relationships.zip
cd ../
