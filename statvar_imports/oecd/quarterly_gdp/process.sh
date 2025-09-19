#!/bin/bash
#
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Usage:
#
# # Run from project root
# bash statvar_imports/oecd/quarterly_gdp/process.sh

set -e

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input/oecd_gdp_data.csv \
  --pv_map=pvmap.csv \
  --config_file=metadata.csv \
  --output_path=output/oecd_quarterly_gdp \
  --output_counters=output/oecd_quarterly_gdp/validation/statvar_counters.csv
