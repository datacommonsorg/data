#!/bin/bash
# Copyright 2026 Google LLC
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

set -e -o pipefail

SCRIPT_DIR=$(dirname "$0")
INPUT_DIR="$SCRIPT_DIR/input_files"

mkdir -p "$INPUT_DIR/country"
mkdir -p "$INPUT_DIR/states"
mkdir -p "$INPUT_DIR/county"

GCS_BASE="gs://unresolved_mcf/cdc/wonder/natality"

echo "Attempting to download latest preprocessed CDC Natality artifacts from GCS..."
if command -v gcloud &> /dev/null; then
    gcloud storage cp "$GCS_BASE/country/*/*.csv" "$INPUT_DIR/country/" || true
    gcloud storage cp "$GCS_BASE/states/*/*.csv" "$INPUT_DIR/states/" || true
    gcloud storage cp "$GCS_BASE/county/*/*.csv" "$INPUT_DIR/county/" || true
fi

# Flatten and rename files to prevent directory collisions during executor GCS upload
for f in "$INPUT_DIR"/country/*.csv; do
    [ -f "$f" ] && mv "$f" "$INPUT_DIR/country_$(basename "$f")"
done
for f in "$INPUT_DIR"/states/*.csv; do
    [ -f "$f" ] && mv "$f" "$INPUT_DIR/state_$(basename "$f")"
done
for f in "$INPUT_DIR"/county/*.csv; do
    [ -f "$f" ] && mv "$f" "$INPUT_DIR/county_$(basename "$f")"
done

# Remove temporary subdirectories so input_files only contains regular files
rm -rf "$INPUT_DIR/country" "$INPUT_DIR/states" "$INPUT_DIR/county"

# If raw zip exists and is an actual archive, extract it
if [ -f "$SCRIPT_DIR/source_data/county.zip" ]; then
    if file "$SCRIPT_DIR/source_data/county.zip" | grep -q "Zip archive"; then
        echo "Extracting raw county source data..."
        unzip -q -o "$SCRIPT_DIR/source_data/county.zip" -d "$INPUT_DIR/" || true
    fi
fi

# Verify that at least some input data files were obtained
FILE_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -type f \( -name "*.csv" -o -name "*.txt" \) | wc -l)
if [ "$FILE_COUNT" -eq 0 ]; then
    echo "ERROR: Download step failed to obtain any data files in $INPUT_DIR" >&2
    exit 1
fi

echo "Download completed successfully with $FILE_COUNT input data files."
