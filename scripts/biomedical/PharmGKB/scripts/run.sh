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
Name: run
Description: This file runs all the scripts that clean each of the data
files in this import. The end result is the data is formatted into CSVs
ready for import alongside paired tMCF files.
"""

#!/bin/bash

# make output directory
mkdir CSVs

# format files
# remove common compounds between chemicals and drugs to reduce run time
cd input/chemicals
cat <(head -n 1 chemicals.tsv) <(comm -23 <(sort chemicals.tsv) <(sort ../drugs/drugs.tsv)) > non_overlapped_chemicals.tsv
cd ../../
python3 scripts/format_chemicals.py input/chemicals/non_overlapped_chemicals.tsv CSVs/chemicals.csv CSVs/chemicals_pharmgkbId_to_dcid.csv

# format drugs
python3 scripts/format_drugs.py input/drugs/drugs.tsv CSVs/drugs.csv CSVs/drugs_pharmgkbId_to_dcid.csv

# format genes
python3 scripts/format_genes.py input/genes/genes.tsv CSVs/genes.csv

# format phenotypes
python3 scripts/format_phenotypes.py input/phenotypes/phenotypes.tsv CSVs/phenotypes.csv

# format variants
python3 scripts/format_variants.py input/variants/variants.tsv CSVs/variants.csv

# format relationships
python3 scripts/format_relationships.py input/relationships/relationships.tsv CSVs/chemicals_pharmgkbId_to_dcid.csv CSVs/drugs_pharmgkbId_to_dcid.csv diseases_pharmgkbId_to_dcid.csv
