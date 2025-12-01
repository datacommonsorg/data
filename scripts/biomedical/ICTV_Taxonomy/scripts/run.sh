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
Name: download
Description: This file runs the python scripts to generate the viral taxonomy
enum mcf file and the csv files for Viruses, Virus Isolates, and Virus Genome 
Segments from the ICTV Master Species List and the Virus Metadata Files.
"""

# !/bin/bash

# make CSV directory to which to output cleaned csv
mkdir -p CSVs

# Command to Generate Taxonomic Rank Enum Schema
python3 scripts/create_virus_taxonomic_ranking_enums.py input/ICTV_Virus_Metadata_Resource.xlsx  ICTV_schema_taxonomic_ranking_enum.mcf

# Commands to Run Scripts to Generate Cleaned CSV Files
python3 scripts/format_virus_master_species_list.py input/ICTV_Virus_Species_List.xlsx CSVs/VirusSpecies.csv

python3 scripts/format_virus_metadata_resource.py input/ICTV_Virus_Metadata_Resource.xlsx CSVs/VirusIsolates.csv CSVs/VirusGenomeSegments.csv > format_virus_metadata_resource.log
