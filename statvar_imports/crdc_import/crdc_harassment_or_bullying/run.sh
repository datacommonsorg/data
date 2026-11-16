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
PV_MAP_FILE="harassment_or_bullying_pvmap.csv"
CONFIG_FILE="harassment_or_bullying_metadata.csv"
OUTPUT_DIR="processed_output"
EXISTING_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
PYTHON_SCRIPT="../../../tools/statvar_importer/stat_var_processor.py"

# Use all available vCPUs (defaults to 16 matching manifest.json resource_limits)
MAX_PARALLEL_JOBS=$(nproc 2>/dev/null || echo 16)

# =================================================================
# EXECUTION LOGIC
# =================================================================

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' not found."
    exit 1
fi

echo "Starting parallel processing of files in $INPUT_DIR (MAX_PARALLEL_JOBS=$MAX_PARALLEL_JOBS)..."
JOB_COUNT=0
FAILED_JOBS=0
PIDS=()

# 1. Process 2024 onwards files dynamically into a single 2024Onwards output
CSV_FILES_2024_ONWARD=$(find "$INPUT_DIR" -maxdepth 1 -type f -name "*.csv" | grep -Ev "_(2012|2014|2018|2021|2022)(_|\.)" | sort | paste -sd, -)

if [ -z "$CSV_FILES_2024_ONWARD" ]; then
    echo "Error: No 2024+ CSV files found in '$INPUT_DIR'."
    exit 1
fi

output_file="$OUTPUT_DIR/crdc_harassment_or_bullying_2024Onwards"
echo "Launching job for 2024Onwards: $CSV_FILES_2024_ONWARD"
python3 "$PYTHON_SCRIPT" \
    --input_data="$CSV_FILES_2024_ONWARD" \
    --pv_map="$PV_MAP_FILE" \
    --config_file="$CONFIG_FILE" \
    --existing_statvar_mcf="$EXISTING_MCF" \
    --output_path="$output_file" \
    --output_counters="${output_file}_counters.txt" \
    --log_level=-2 \
    --log_every_n=10000 &
PIDS+=("$!")
JOB_COUNT=$((JOB_COUNT + 1))

# 2. Sort remaining (2012-2022) CSV files by size descending so the largest files start first
while IFS= read -r base_name; do
    [ -z "$base_name" ] && continue
    input_file="$INPUT_DIR/$base_name"
    if [ -f "$input_file" ] && echo "$base_name" | grep -Eq "_(2012|2014|2018|2021|2022)(_.*)?\.csv$"; then
        # If we reached the max number of parallel jobs, wait for a slot to open
        while [[ $(jobs -r -p | wc -l) -ge $MAX_PARALLEL_JOBS ]]; do
            wait -n 2>/dev/null || sleep 1
        done

        filename_only="${base_name%.*}"
        output_file="$OUTPUT_DIR/${filename_only}"

        echo "Launching job for: $input_file"

        python3 "$PYTHON_SCRIPT" \
            --input_data="$input_file" \
            --pv_map="$PV_MAP_FILE" \
            --config_file="$CONFIG_FILE" \
            --existing_statvar_mcf="$EXISTING_MCF" \
            --output_path="$output_file" \
            --output_counters="${output_file}_counters.txt" \
            --log_level=-2 \
            --log_every_n=10000 &

        PIDS+=("$!")
        JOB_COUNT=$((JOB_COUNT + 1))
    fi
done < <(find "$INPUT_DIR" -maxdepth 1 -type f -name "*.csv" -printf '%s\t%f\n' | sort -rn -k1,1 -k2,2 | cut -f2-)

echo "---"
echo "Waiting for remaining $(jobs -r -p | wc -l) of $JOB_COUNT jobs to complete..."

# Wait for all spawned processes and capture exit codes to identify failures
for pid in "${PIDS[@]}"; do
    wait "$pid" || FAILED_JOBS=$((FAILED_JOBS + 1))
done

if [ "$FAILED_JOBS" -gt 0 ]; then
    echo "Processing complete with $FAILED_JOBS errors."
    exit 1
else
    echo "All parallel processing jobs completed successfully. Output files are in $OUTPUT_DIR"
fi
