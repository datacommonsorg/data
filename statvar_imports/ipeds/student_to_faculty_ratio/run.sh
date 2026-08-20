#!/bin/bash
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

# =================================================================
# CONFIGURATION SECTION
# =================================================================
INPUT_DIR="./input_files"
PV_MAP_FILE="student_faculty_ratio_pvmap.csv"
CONFIG_FILE="student_faculty_ratio_metadata.csv"
OUTPUT_DIR="processed_output"
EXISTING_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
PYTHON_SCRIPT="../../../tools/statvar_importer/stat_var_processor.py"

# Concurrency limit for background processing jobs
MAX_CONCURRENT_JOBS=4  

# =================================================================
# EXECUTION LOGIC
# =================================================================

mkdir -p "$OUTPUT_DIR"
mkdir -p counters

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' not found."
    exit 1
fi

echo "Starting parallel processing..."

JOB_COUNT=0
EXIT_STATUS=0

for input_file in "$INPUT_DIR"/*; do
    if [ -f "$input_file" ]; then
        
        # Concurrency control logic to prevent system overload
        while [ "$(jobs -rp | wc -l)" -ge "$MAX_CONCURRENT_JOBS" ]; do
            if ! wait -n; then
                EXIT_STATUS=1
            fi
        done

        base_name=$(basename "$input_file")
        filename_only="${base_name%.*}"
        
        # Remove "_data" from the filename for the output base
        # Example: student_faculty_ratio_data_2009 -> student_faculty_ratio_2009
        clean_base="${filename_only/_data/}" 
        
        # We pass the base path; the tool usually appends extensions
        output_base_path="$OUTPUT_DIR/${clean_base}"
        
        echo "[$(date +%T)] Processing: $base_name"

        python3 "$PYTHON_SCRIPT" \
            --input_data="$input_file" \
            --pv_map="$PV_MAP_FILE" \
            --config_file="$CONFIG_FILE" \
            --existing_statvar_mcf="$EXISTING_MCF" \
            --output_path="$output_base_path" \
            --output_counters="counters/${clean_base}_counters.csv" \
            --log_level=-2 \
            --log_every_n=1000 &
        
        JOB_COUNT=$((JOB_COUNT + 1))
    fi
done

echo "---"
echo "Waiting for background jobs to complete..."

# Wait for all remaining background jobs to finish and capture any failures
while [ "$(jobs -p | wc -l)" -gt 0 ]; do
    if ! wait -n; then
        EXIT_STATUS=1
    fi
done

# =================================================================
# POST-PROCESSING: CLEANUP & RENAME
# =================================================================
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Processing successful. Finalizing file names..."

    # 1. Dynamically pick the first available .tmcf file and rename it to student_faculty_ratio.tmcf
    FIRST_TMCF=$(find "$OUTPUT_DIR" -type f -name "*.tmcf" | head -n 1)
    if [ -n "$FIRST_TMCF" ]; then
        if [ "$FIRST_TMCF" != "$OUTPUT_DIR/student_faculty_ratio.tmcf" ]; then
            mv "$FIRST_TMCF" "$OUTPUT_DIR/student_faculty_ratio.tmcf"
        fi
        # Delete any remaining duplicate .tmcf files
        find "$OUTPUT_DIR" -type f -name "*.tmcf" ! -name "student_faculty_ratio.tmcf" -delete
    else
        echo "Error: No .tmcf files found in $OUTPUT_DIR"
        EXIT_STATUS=1
    fi

    # 2. Normalize CSV file names (e.g. fix any double extensions like .csv.csv) for all years
    for csv_file in "$OUTPUT_DIR"/*.csv.csv; do
        if [ -f "$csv_file" ]; then
            mv "$csv_file" "${csv_file%.csv}"
        fi
    done

    echo "Cleanup complete."
    echo "Results: "
    echo "  - $OUTPUT_DIR/student_faculty_ratio.tmcf"
    echo "  - $OUTPUT_DIR/*.csv"
else
    echo "Cleanup skipped due to job failures."
fi

exit $EXIT_STATUS