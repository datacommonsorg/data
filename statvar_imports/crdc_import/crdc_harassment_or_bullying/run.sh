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

set -euo pipefail

# =================================================================
# CONFIGURATION SECTION
# =================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${INPUT_DIR:-$SCRIPT_DIR/preprocessed_files}"
PV_MAP_FILE="${PV_MAP_FILE:-$SCRIPT_DIR/harassment_or_bullying_pvmap.csv}"
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/harassment_or_bullying_metadata.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/processed_output}"
EXISTING_MCF="${EXISTING_STATVAR_MCF:-gs://unresolved_mcf/scripts/statvar/stat_vars.mcf}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-$SCRIPT_DIR/../../../tools/statvar_importer/stat_var_processor.py}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Use all available vCPUs (defaults to 16 matching manifest.json resource_limits)
MAX_PARALLEL_JOBS="${MAX_PARALLEL_JOBS:-$(nproc 2>/dev/null || echo 16)}"

# =================================================================
# PRE-FLIGHT INPUT VERIFICATION
# =================================================================

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Preprocessed input directory '$INPUT_DIR' not found." >&2
    exit 1
fi

REQUIRED_HISTORICAL_FILES=(
    "crdc_harassment_or_bullying_2012_part_01.csv"
    "crdc_harassment_or_bullying_2012_part_02.csv"
    "crdc_harassment_or_bullying_2012_part_03.csv"
    "crdc_harassment_or_bullying_2012_part_04.csv"
    "crdc_harassment_or_bullying_2012_part_05.csv"
    "crdc_harassment_or_bullying_2012_part_06.csv"
    "crdc_harassment_or_bullying_2014.csv"
    "crdc_harassment_or_bullying_2018.csv"
    "crdc_harassment_or_bullying_2021.csv"
    "crdc_harassment_or_bullying_2022.csv"
)

MISSING_INPUTS=0
for req_file in "${REQUIRED_HISTORICAL_FILES[@]}"; do
    if [ ! -s "$INPUT_DIR/$req_file" ]; then
        echo "Error: Missing or empty required input file '$INPUT_DIR/$req_file'." >&2
        MISSING_INPUTS=$((MISSING_INPUTS + 1))
    fi
done

# Positively match 2024+ CSV files for the 2024Onwards partition.
CSV_FILES_2024_ONWARD=$(
    find "$INPUT_DIR" -maxdepth 1 -type f -name "*.csv" \
        | grep -E "_(202[4-9]|20[3-9][0-9])(_part_[0-9]+)?\.csv$" \
        | sort \
        | paste -sd, - || true
)

if [ -z "$CSV_FILES_2024_ONWARD" ]; then
    echo "Error: No 2024+ CSV files found in '$INPUT_DIR'." >&2
    MISSING_INPUTS=$((MISSING_INPUTS + 1))
fi

if ! echo "$CSV_FILES_2024_ONWARD" | grep -Eq "_2024(_part_[0-9]+)?\.csv(,|$)"; then
    echo "Error: Baseline 2024 CSV file is missing from '$INPUT_DIR'." >&2
    MISSING_INPUTS=$((MISSING_INPUTS + 1))
fi

if [ "$MISSING_INPUTS" -gt 0 ]; then
    echo "Aborting before StatVar processing due to $MISSING_INPUTS missing required input check(s)." >&2
    exit 1
fi

# =================================================================
# EXECUTION LOGIC
# =================================================================

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "Starting parallel processing of files in $INPUT_DIR (MAX_PARALLEL_JOBS=$MAX_PARALLEL_JOBS)..."
JOB_COUNT=0
FAILED_JOBS=0
PIDS=()

# 1. Process 2024 onwards files dynamically into a single 2024Onwards output
output_file="$OUTPUT_DIR/crdc_harassment_or_bullying_2024Onwards"
echo "Launching job for 2024Onwards: $CSV_FILES_2024_ONWARD"
"$PYTHON_BIN" "$PYTHON_SCRIPT" \
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

# 2. Sort remaining (2012-2022) CSV files by size descending so largest files start first
while IFS= read -r base_name; do
    [ -z "$base_name" ] && continue
    input_file="$INPUT_DIR/$base_name"
    if [ -f "$input_file" ] && echo "$base_name" | grep -Eq "_(2012|2014|2018|2021|2022)(_part_[0-9]+)?\.csv$"; then
        while [[ $(jobs -r -p | wc -l) -ge $MAX_PARALLEL_JOBS ]]; do
            wait -n 2>/dev/null || sleep 1
        done

        filename_only="${base_name%.*}"
        output_file="$OUTPUT_DIR/${filename_only}"

        echo "Launching job for: $input_file"

        "$PYTHON_BIN" "$PYTHON_SCRIPT" \
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

for pid in "${PIDS[@]}"; do
    wait "$pid" || FAILED_JOBS=$((FAILED_JOBS + 1))
done

if [ "$FAILED_JOBS" -gt 0 ]; then
    echo "Processing failed with $FAILED_JOBS StatVar processor error(s)." >&2
    exit 1
fi

# =================================================================
# POST-FLIGHT OUTPUT CONTRACT VERIFICATION
# =================================================================

REQUIRED_TMCFS=(
    "crdc_harassment_or_bullying_2012_part_01.tmcf"
    "crdc_harassment_or_bullying_2014.tmcf"
    "crdc_harassment_or_bullying_2018.tmcf"
    "crdc_harassment_or_bullying_2021.tmcf"
    "crdc_harassment_or_bullying_2022.tmcf"
    "crdc_harassment_or_bullying_2024Onwards.tmcf"
)

REQUIRED_CSVS=(
    "crdc_harassment_or_bullying_2012_part_01.csv"
    "crdc_harassment_or_bullying_2012_part_02.csv"
    "crdc_harassment_or_bullying_2012_part_03.csv"
    "crdc_harassment_or_bullying_2012_part_04.csv"
    "crdc_harassment_or_bullying_2012_part_05.csv"
    "crdc_harassment_or_bullying_2012_part_06.csv"
    "crdc_harassment_or_bullying_2014.csv"
    "crdc_harassment_or_bullying_2018.csv"
    "crdc_harassment_or_bullying_2021.csv"
    "crdc_harassment_or_bullying_2022.csv"
    "crdc_harassment_or_bullying_2024Onwards.csv"
)

for tmcf in "${REQUIRED_TMCFS[@]}"; do
    if [ ! -s "$OUTPUT_DIR/$tmcf" ]; then
        echo "Error: Expected output TMCF '$OUTPUT_DIR/$tmcf' is missing or empty." >&2
        exit 1
    fi
done

for csv_out in "${REQUIRED_CSVS[@]}"; do
    if [ ! -s "$OUTPUT_DIR/$csv_out" ] || [ "$(wc -l < "$OUTPUT_DIR/$csv_out")" -le 1 ]; then
        echo "Error: Expected output CSV '$OUTPUT_DIR/$csv_out' is missing or has 0 data rows." >&2
        exit 1
    fi
done

echo "All $JOB_COUNT processing jobs and output contract checks completed successfully. Output files are in $OUTPUT_DIR"
