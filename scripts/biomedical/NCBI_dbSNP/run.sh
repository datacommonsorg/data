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

#!/bin/bash

# make all required directories
mkdir -p output
mkdir -p output/GCF25
mkdir -p output/GCF40
mkdir -p output/GCF40/hg38
mkdir -p output/GCF40/hg38alleledisease
mkdir -p output/GCF40/hg38alleledrug
mkdir -p output/GCF40/hg38alleles
mkdir -p output/GCF40/hg38freq
mkdir -p output/freq

echo "File split started"
sh split_files.sh
echo "Splitting  Completed"

# Command
echo "Running python script"

python3 scripts/process_medgen.py
python3 scripts/process_genome_assembly_report.py
python3 scripts/process_gene_condition_source.py

echo "Start background process"
sh background_process.sh scripts/process_dbsnp_hg19_positions.py input/GCF25/
sh background_process.sh scripts/process_dbsnp_hg38.py input/GCF40/
sh background_process.sh scripts/process_dbsnp_freq.py input/freq/
echo "Background process completed"
