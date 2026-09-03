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

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================================================="
echo "California School Performance (CAASPP) Data Ingestion Pipeline"
echo "=========================================================================="

DOWNLOAD_ARGS=("$@")
if [ $# -eq 0 ]; then
  # Default to downloading all available years
  DOWNLOAD_ARGS=("--years=all" "--data_mode=all_students")
fi

echo "Step 1: Downloading and normalizing raw CAASPP research data..."
python3 download.py "${DOWNLOAD_ARGS[@]}"
echo "--- Download & normalization complete ---"
echo ""

echo "Step 2: Processing normalized data with StatVarDataProcessor..."
mkdir -p output_files

TOOLS_DIR="$( cd "$SCRIPT_DIR/../../../tools/statvar_importer" && pwd )"
CONFIG_DIR="$SCRIPT_DIR/config"
PVMAP="$CONFIG_DIR/california_school_performance_pvmap.csv"
METADATA="$CONFIG_DIR/california_school_performance_metadata.csv"
EXISTING_MCF="$CONFIG_DIR/california_school_performance_stat_vars.mcf"

# If the master all-years normalized file exists, process it to generate the complete dataset
if [ -f "$SCRIPT_DIR/input_files/sb_ca_all_years_normalized.txt" ]; then
  echo "--------------------------------------------------------------------------"
  echo "Processing complete multi-year dataset: sb_ca_all_years_normalized.txt"
  echo "--------------------------------------------------------------------------"
  PYTHONPATH="$TOOLS_DIR" python3 "$TOOLS_DIR/stat_var_processor.py" \
    --input_data="$SCRIPT_DIR/input_files/sb_ca_all_years_normalized.txt" \
    --pv_map="$PVMAP" \
    --config_file="$METADATA" \
    --existing_statvar_mcf="$EXISTING_MCF" \
    --output_path="$SCRIPT_DIR/output_files/california_school_performance_all_years_output"
fi

# Also process individual year normalized files
for input_file in "$SCRIPT_DIR"/input_files/sb_ca[0-9]*_normalized.txt; do
  [ -e "$input_file" ] || continue
  
  filename=$(basename "$input_file")
  year=$(echo "$filename" | grep -o '[0-9]\{4\}')
  output_path="$SCRIPT_DIR/output_files/california_school_performance_${year}_output"
  
  echo "--------------------------------------------------------------------------"
  echo "Processing Year $year: $filename"
  echo "Output:          $output_path"
  echo "--------------------------------------------------------------------------"
  
  PYTHONPATH="$TOOLS_DIR" python3 "$TOOLS_DIR/stat_var_processor.py" \
    --input_data="$input_file" \
    --pv_map="$PVMAP" \
    --config_file="$METADATA" \
    --existing_statvar_mcf="$EXISTING_MCF" \
    --output_path="$output_path"
done


echo ""
echo "=========================================================================="
echo "Pipeline execution completed successfully."
echo "Outputs generated in $SCRIPT_DIR/output_files/"
echo "=========================================================================="
