#!/bin/bash
# Copyright 2025 Google LLC
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

# Fail on any error.
set -e

# Run the download script first


# Create the output directory if it doesn't exist
mkdir -p output_files

# Define constants
STAT_VAR_PROCESSOR="../../tools/statvar_importer/stat_var_processor.py"
EXISTING_STATVAR_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
CONFIG_FILE="college_admissions_ipeds_metadata.csv"

# Process each year's data file
for YEAR in {2014..2023}
do
    echo "Processing data for the year ${YEAR}"
    
    INPUT_DATA="input_files/college_admissions_${YEAR}.csv"
    PV_MAP="pv_map/college_admissions_ipeds_pv_map_${YEAR}.csv"
    OUTPUT_PATH="output_files/admissions_output_${YEAR}"
    
    python3 "${STAT_VAR_PROCESSOR}" \
        --existing_statvar_mcf="${EXISTING_STATVAR_MCF}" \
        --input_data="${INPUT_DATA}" \
        --pv_map="${PV_MAP}" \
        --config_file="${CONFIG_FILE}" \
        --output_path="${OUTPUT_PATH}"
done

echo "All years processed successfully."

