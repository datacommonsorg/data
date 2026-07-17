#!/bin/bash
# Copyright 2026 Google LLC
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

set -e
mkdir -p input_files
mkdir -p output_files

python3 data_download.py --output_path=./input_files/finland_census_input.csv

python3 ../../tools/statvar_importer/stat_var_processor.py --input_data="input_files/*.csv" --pv_map="finland_census_pvmap.csv" --config_file="finland_census_metadata.csv" --output_path="output_files/finland_census_output" --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
