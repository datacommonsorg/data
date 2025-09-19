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
# # Run with default start year (2020) and end year (current year)
# bash statvar_imports/oecd/quarterly_gdp/download.sh
#
# # Run with custom start and end years from project root
# START_YEAR=2018 END_YEAR=2022 bash statvar_imports/oecd/quarterly_gdp/download.sh

set -e

# --- Configuration ---
AGENCY_ID="OECD.SDD.NAD"
DATAFLOW_ID="DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD"
ENDPOINT="https://sdmx.oecd.org/public/rest/"
SCRIPT_DIR=$(realpath $(dirname "${BASH_SOURCE[0]}"))
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/../../../")
DEST_DIR="$SCRIPT_DIR/input"

# --- Environment Variables ---
START_YEAR="${START_YEAR:-2020}"
END_YEAR="${END_YEAR:-$(date +%Y)}"

# --- Create Destination Directory ---
mkdir -p "$DEST_DIR"

# --- Download Metadata ---
echo "--- Step 1: Starting Metadata Download ---"
python3 "$PROJECT_ROOT/tools/sdmx_import/sdmx_cli.py" download-metadata \
    --endpoint="$ENDPOINT" \
    --agency="$AGENCY_ID" \
    --dataflow="$DATAFLOW_ID" \
    --output_path="$DEST_DIR/oecd_gdp_metadata.xml"

# --- Download Data ---
echo -e "\n--- Step 2: Starting Data Download ---"
python3 "$PROJECT_ROOT/tools/sdmx_import/sdmx_cli.py" download-data \
    --endpoint="$ENDPOINT" \
    --agency="$AGENCY_ID" \
    --dataflow="$DATAFLOW_ID" \
    --output_path="$DEST_DIR/oecd_gdp_data.csv" \
    --key="TRANSACTION:B1GQ" \
    --param="startPeriod:$START_YEAR" \
    --param="endPeriod:$END_YEAR"

echo -e "\n--- Download Complete ---"