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
# CONFIGURATION SECTION
# =================================================================
INPUT_DIR="./input_files"
PV_MAP_FILE="student_faculty_ratio_pvmap.csv"
CONFIG_FILE="student_faculty_ratio_metadata.csv"
OUTPUT_DIR="processed_output"
EXISTING_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
PYTHON_SCRIPT="../../../tools/statvar_importer/stat_var_processor.py"

# TODO: Limit the concurrency to a defined number of jobs
MAX_CONCURRENT_JOBS=4  

# =================================================================
# EXECUTION LOGIC
# =================================================================

mkdir -p "$OUTPUT_DIR"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' not found."
    exit 1
fi

echo "Starting parallel processing..."

PIDS=()
JOB_COUNT=0

for input_file in "$INPUT_DIR"/*; do
    if [ -f "$input_file" ]; then
        
        # TODO: Concurrency control logic to prevent system overload
        while [ "$(jobs -rp | wc -l)" -ge "$MAX_CONCURRENT_JOBS" ]; do
            wait -n
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
            --log_level=-2 \
            --log_every_n=1000 &
        
        PIDS+=($!) 
        JOB_COUNT=$((JOB_COUNT + 1))
    fi
done

echo "---"
echo "Waiting for background jobs to complete..."

# TODO: Check for exit codes of background processes
EXIT_STATUS=0
for pid in "${PIDS[@]}"; do
    wait "$pid"
    STATUS=$?
    if [ $STATUS -ne 0 ]; then
        echo "Error: Job PID $pid failed (Exit Code: $STATUS)"
        EXIT_STATUS=1
    fi
done

# =================================================================
# POST-PROCESSING: CLEANUP & RENAME
# =================================================================
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Processing successful. Finalizing file names..."

    # 1. Delete all .tmcf files EXCEPT the 2009 one
    find "$OUTPUT_DIR" -type f -name "*.tmcf" ! -name "*2009*" -delete

    # 2. Rename the 2009 tmcf file to exactly student_faculty_ratio.tmcf
    # Note: If the script appended .csv.tmcf, this finds and fixes it
    TMCF_2009=$(find "$OUTPUT_DIR" -type f -name "*2009*.tmcf" | head -n 1)
    if [ -n "$TMCF_2009" ]; then
        mv "$TMCF_2009" "$OUTPUT_DIR/student_faculty_ratio.tmcf"
    fi

    # 3. Ensure CSV files are named correctly (removing any double extensions like .csv.csv)
    # This specifically looks for the 2009 csv output
    CSV_2009=$(find "$OUTPUT_DIR" -type f -name "*2009*.csv" | head -n 1)
    if [ -n "$CSV_2009" ]; then
        mv "$CSV_2009" "$OUTPUT_DIR/student_faculty_ratio_2009.csv"
    fi

    echo "Cleanup complete."
    echo "Results: "
    echo "  - $OUTPUT_DIR/student_faculty_ratio.tmcf"
    echo "  - $OUTPUT_DIR/student_faculty_ratio_2009.csv"
else
    echo "Cleanup skipped due to job failures."
fi

exit $EXIT_STATUS