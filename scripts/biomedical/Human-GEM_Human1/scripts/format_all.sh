# Copyright 2021 Google LLC
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

'''
Author: Khoa Hoang
Date: 08/11/2021
Name: format_all.sh
Description: This script runs all python scripts 
to format all human1 data files
'''
#!/bin/bash
python map_human1_hmdb.py metabolites.tsv recon-store-metabolites-1.tsv hmdb.csv
python format_metabolites.py metabolites.tsv reactantRoles.tsv productRoles.tsv humanGEM_HMDB_map.csv
python format_genes.py genes.tsv geneRoles.tsv
python format_reactions.py reactions.tsv
python format_groups.py groups.tsv groupMemberships.tsv
