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

set -e

# --- Configuration ---
AGENCY_ID="OECD.SDD.NAD"
DATAFLOW_ID="DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD"
ENDPOINT="https://sdmx.oecd.org/public/rest/"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
OUTPUT_DIR="$SCRIPT_DIR/output"

# --- Environment Variables ---
START_YEAR="${START_YEAR:-2020}"
END_YEAR="${END_YEAR:-2025}"

# --- Create Output Directory ---
mkdir -p "$OUTPUT_DIR"

# --- Download Metadata ---
echo "--- Step 1: Starting Metadata Download ---"
python3 tools/sdmx_import/sdmx_cli.py download-metadata \
    --endpoint="$ENDPOINT" \
    --agency="$AGENCY_ID" \
    --dataflow="$DATAFLOW_ID" \
    --output_path="$OUTPUT_DIR/oecd_gdp_full_metadata.xml"

# --- Download Data ---
echo -e "\n--- Step 2: Starting Full Data Download ---"
python3 tools/sdmx_import/sdmx_cli.py download-data \
    --endpoint="$ENDPOINT" \
    --agency="$AGENCY_ID" \
    --dataflow="$DATAFLOW_ID" \
    --output_path="$OUTPUT_DIR/oecd_gdp_full_data.csv" \
    --param="startPeriod:$START_YEAR" \
    --param="endPeriod:$END_YEAR"

echo -e "\n--- Download Complete ---"
