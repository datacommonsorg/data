#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

SCRIPT_PATH=$(realpath "$(dirname "$0")")
PROCESSOR_PY="$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py"

mkdir -p "$SCRIPT_PATH/output_files" "$SCRIPT_PATH/counters"

# --- Stage existing_statvar_mcf once locally to avoid 9 sequential GCS downloads ---
EXISTING_STATVAR_MCF_SRC="${EXISTING_STATVAR_MCF:-gs://unresolved_mcf/scripts/statvar/stat_vars.mcf}"
LOCAL_STAT_VARS_MCF=""
cleanup() {
  if [[ -n "$LOCAL_STAT_VARS_MCF" && -f "$LOCAL_STAT_VARS_MCF" ]]; then
    rm -f "$LOCAL_STAT_VARS_MCF"
  fi
}
trap cleanup EXIT

if [[ "$EXISTING_STATVAR_MCF_SRC" == gs://* ]]; then
  LOCAL_STAT_VARS_MCF=$(mktemp "${TMPDIR:-/tmp}/stat_vars_XXXXXX.mcf")
  python3 - "$SCRIPT_PATH/../../../util" "$EXISTING_STATVAR_MCF_SRC" "$LOCAL_STAT_VARS_MCF" <<'PY'
import os
import sys
import time

sys.path.insert(0, sys.argv[1])
import file_util  # pylint: disable=import-error

src_uri, dst_path = sys.argv[2], sys.argv[3]
for attempt in range(1, 4):
    try:
        file_util.file_copy(src_uri, dst_path)
        if os.path.getsize(dst_path) > 0:
            break
        raise RuntimeError(f"Copied empty MCF from {src_uri}")
    except Exception:
        if attempt == 3:
            raise
        time.sleep(5 * attempt)
PY
  EXISTING_STATVAR_MCF_PATH="$LOCAL_STAT_VARS_MCF"
else
  EXISTING_STATVAR_MCF_PATH="$EXISTING_STATVAR_MCF_SRC"
fi

if [[ ! -s "$EXISTING_STATVAR_MCF_PATH" ]]; then
  echo "Error: Existing StatVar MCF file $EXISTING_STATVAR_MCF_PATH is missing or empty!"
  exit 1
fi

# --- Pre-flight verification of all required CRDC input files ---
SUBJECTS=(
  "Advanced_Mathematics"
  "Algebra_II"
  "Biology"
  "Calculus"
  "Chemistry"
  "Geometry"
  "Physics"
)

for year in 2010 2012; do
  for subject in "${SUBJECTS[@]}"; do
    req_file="$SCRIPT_PATH/input_files/${year}_${subject}.xlsx"
    if [[ ! -s "$req_file" ]]; then
      echo "Error: Required input file $req_file is missing or empty!"
      exit 1
    fi
  done
done

SINGLE_2016_FILE="$SCRIPT_PATH/input_files/2016_School_data.csv"
if [[ ! -s "$SINGLE_2016_FILE" ]]; then
  echo "Error: Required input file $SINGLE_2016_FILE is missing or empty!"
  exit 1
fi

for year in 2018 2021 2022 2024; do
  for subject in "${SUBJECTS[@]}"; do
    req_file="$SCRIPT_PATH/input_files/${year}_${subject}.csv"
    if [[ ! -s "$req_file" ]]; then
      echo "Error: Required input file $req_file is missing or empty!"
      exit 1
    fi
  done
done

LEGACY_XLSX_FILES=$(find "$SCRIPT_PATH/input_files" -maxdepth 1 -name "*.xlsx" | sort | paste -sd, -)

# --- 1. Process 2010 and 2012 Files (Older XLSX format) ---
python3 "$PROCESSOR_PY" \
  --input_data="$LEGACY_XLSX_FILES" \
  --pv_map="$SCRIPT_PATH/maths_and_science_pvmap.csv" \
  --config_file="$SCRIPT_PATH/metadata.csv" \
  --existing_statvar_mcf="$EXISTING_STATVAR_MCF_PATH" \
  --output_path="$SCRIPT_PATH/output_files/maths_and_science_2010_2012_output" \
  --output_counters="$SCRIPT_PATH/counters/maths_and_science_2010_2012_counters.csv" \
  --recon_property=variableMeasured \
  --log_level=-2 \
  --log_every_n=1000 || \
  { echo "Error: Processing maths_and_science files for the year 2010 to 2012 failed!"; exit 1; }

# --- 2. Process 2016 File (Separate CSV) ---
python3 "$PROCESSOR_PY" \
  --input_data="$SINGLE_2016_FILE" \
  --pv_map="$SCRIPT_PATH/maths_and_science_pvmap.csv" \
  --config_file="$SCRIPT_PATH/metadata.csv" \
  --existing_statvar_mcf="$EXISTING_STATVAR_MCF_PATH" \
  --output_path="$SCRIPT_PATH/output_files/maths_and_science_2016_output" \
  --output_counters="$SCRIPT_PATH/counters/maths_and_science_2016_counters.csv" \
  --recon_property=variableMeasured \
  --log_level=-2 \
  --log_every_n=1000 || \
  { echo "Error: Processing maths_and_science files for the year 2016 failed!"; exit 1; }

# --- 3. Process 2018 onwards Files (Combined CSVs for each course) ---
# Explicitly verified for 2018, 2021, 2022, and 2024, and dynamically includes future years.
run_course_2018_onwards() {
  local file_suffix="$1"
  local output_prefix="$2"
  local label="$3"

  local csv_files
  csv_files=$(find "$SCRIPT_PATH/input_files" -maxdepth 1 -name "*_${file_suffix}.csv" | sort | paste -sd, -)
  if [[ -z "$csv_files" ]]; then
    echo "Error: No CSV files found for ${label} (2018 onwards)!"
    exit 1
  fi

  python3 "$PROCESSOR_PY" \
    --input_data="$csv_files" \
    --pv_map="$SCRIPT_PATH/maths_and_science_pvmap.csv" \
    --config_file="$SCRIPT_PATH/metadata.csv" \
    --existing_statvar_mcf="$EXISTING_STATVAR_MCF_PATH" \
    --output_path="$SCRIPT_PATH/output_files/${output_prefix}" \
    --output_counters="$SCRIPT_PATH/counters/${output_prefix}_counters.csv" \
    --recon_property=variableMeasured \
    --log_level=-2 \
    --log_every_n=1000 || \
    { echo "Error: Processing ${label} files for the year 2018 onwards failed!"; exit 1; }
}

run_course_2018_onwards "Advanced_Mathematics" "advanced_mathematics_2018_onwards_output" "Advanced mathematics"
run_course_2018_onwards "Algebra_II" "algebra2_2018_onwards_output" "Algebra II"
run_course_2018_onwards "Biology" "biology_2018_onwards_output" "Biology"
run_course_2018_onwards "Calculus" "calculus_2018_onwards_output" "Calculus"
run_course_2018_onwards "Chemistry" "chemistry_2018_onwards_output" "Chemistry"
run_course_2018_onwards "Geometry" "geometry_2018_onwards_output" "Geometry"
run_course_2018_onwards "Physics" "physics_2018_onwards_output" "Physics"

echo "All processing steps completed successfully."
exit 0
