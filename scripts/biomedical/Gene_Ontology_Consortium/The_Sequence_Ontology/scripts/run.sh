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
Date: 05/10/2024
Name: run
Description: This file formats The Sequence Ontology json file into a
CSV for import into the Data Commons knowledge graph. It preserves the
parent-child relationships between nodes, node information, and alternative
identifiers. It also includes links to corresponding MeSHDescriptor nodes.
"""

#!/bin/bash

mkdir -p CSV

# extract the node information for the sequence
python3 The_Sequence_Ontology/scripts/format_the_sequence_ontology.py input/so.json CSV/the_sequence_ontology.csv
