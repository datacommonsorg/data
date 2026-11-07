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

# Author: Pradeep Kumar Krishnaswamy
# Date: 16-Jul-2024


# !/bin/bash

# make output directory to save enmu mcf & cleaned csv
mkdir -p output
mkdir -p input/gene_info
mkdir -p output/gene_info
mkdir -p input/gene_neighbors
mkdir -p output/gene_neighbors
mkdir -p input/gene2go
mkdir -p output/gene2go
mkdir -p input/gene2accession
mkdir -p output/gene2accession

echo "Splitting Gene Info file"
split -l 3750000 input/gene_info.txt  input/gene_info/gene_info_shard_ --additional-suffix=.txt

echo "Splitting ene neighbors file"
split -l 7500000 input/gene_neighbors.txt  input/gene_neighbors/gene_neighbors_shard_ --additional-suffix=.txt

echo "Splitting Gene Go file"
split -l 7500000 input/gene2go.txt  input/gene2go/gene2go_shard_ --additional-suffix=.txt

echo "Splitting Gene Accession file"
split -l 7500000 input/gene2accession.txt  input/gene2accession/gene2accession_shard_ --additional-suffix=.txt

echo "Splitting  Completed"

# Command
echo "Running python script"
python3 scripts/format_ncbi_gene.py --root=$PWD