# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


#!/bin/bash

# =================================================================
# CONFIGURATION SECTION - PLEASE EDIT THESE PATHS
# =================================================================

INPUT_DIR="./input_files"
PV_MAP_FILE="harassment_and_bullying_pvmap.csv"
CONFIG_FILE="harassment_or_bullying_metadata.csv"
OUTPUT_DIR="processed_output" 
EXISTING_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
PYTHON_SCRIPT="../../../tools/statvar_importer/stat_var_processor.py"

# TODO: Limit concurrency to avoid overloading system resources
MAX_PARALLEL_JOBS=4

# =================================================================
# EXECUTION LOGIC
# =================================================================

mkdir -p "$OUTPUT_DIR"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' not found."
    exit 1
fi

echo "Starting parallel processing of files in $INPUT_DIR..."
JOB_COUNT=0
FAILED_JOBS=0

for input_file in "$INPUT_DIR"/*; do
    if [ -f "$input_file" ]; then
        
        base_name=$(basename "$input_file")
        filename_only="${base_name%.*}"
        output_file="$OUTPUT_DIR/${filename_only}"
        
        echo "Launching job for: $input_file"
        
        python3 "$PYTHON_SCRIPT" \
            --input_data="$input_file" \
            --pv_map="$PV_MAP_FILE" \
            --config_file="$CONFIG_FILE" \
            --existing_statvar_mcf="$EXISTING_MCF" \
            --output_path="$output_file" &
        
        JOB_COUNT=$((JOB_COUNT + 1))

        # TODO: Check job status and limit concurrency
        # If we reached the max number of parallel jobs, wait for at least one to finish
        if [[ $(jobs -r -p | wc -l) -ge $MAX_PARALLEL_JOBS ]]; then
            wait -n
        fi
    fi
done

echo "---"
echo "Waiting for remaining $(jobs -r -p | wc -l) jobs to complete..."

# TODO: Check job status of all background processes
# Wait for all processes and capture exit codes to identify failures
for job in $(jobs -p); do
    wait "$job" || FAILED_JOBS=$((FAILED_JOBS + 1))
done

if [ "$FAILED_JOBS" -gt 0 ]; then
    echo "Processing complete with $FAILED_JOBS errors."
    exit 1
else
    echo "All parallel processing jobs completed successfully. Output files are in $OUTPUT_DIR"
fi