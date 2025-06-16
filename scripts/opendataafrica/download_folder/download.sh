#!/bin/bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -xe
COUNTRY=""
DATASETS=()
SELECTED_DATASETS=()
MAX_RETRIES=5                     # Maximum number of retries
RETRY_DELAY=15                    # Seconds to wait between retries

function download_key_families() {
  if [ -f "$WORKING_DIR/key_family.xml" ] && [ $(stat -c%s "$WORKING_DIR/key_family.xml") -gt 0 ]; then
    echo "File $WORKING_DIR/key_family.xml already exists. Skipping download."
    return
  fi
  curl -s --location "https://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx" \
    --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9;v=b3;q=0.7' \
    --header 'Accept-Encoding: gzip, deflate, br, zstd' \
    --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
    --output "$WORKING_DIR/key_family.xml" \
    --compressed
}

function extract_key_families() {
  DATASETS=($(jq -r '."message:Structure"."message:KeyFamilies".KeyFamily.[]."@id"' "$WORKING_DIR/key_family.json"))
}

function download_and_convert_dataset() {
  local dataset="$1" # Pass dataset as an argument
  for i in $(seq 1 $((MAX_RETRIES + 1))); do
    echo "Attempt $dataset $i of $((MAX_RETRIES + 1))..."
    if curl -s --location "http://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx/data/${dataset}" \
      --header 'Accept: text/html,application/xhtml+xml,application/xml' \
      --header 'Accept-Encoding: gzip, deflate, br, zstd' \
      --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
      --output "$WORKING_DIR/${dataset}.xml" \
      --compressed; then
      echo "Download completed for $dataset"
      local json_output_file="$WORKING_DIR/${dataset}.json"
      local csv_output_file="$WORKING_DIR/${dataset}.csv"
        
      local xml_to_json_script_path="../../../util/xml_to_json.py"
      local json_to_csv_script_path="../../../scripts/opendataafrica/download_folder/json_to_csv.py"
      if python3 "$xml_to_json_script_path" "$WORKING_DIR/${dataset}.xml" "$json_output_file"; then
        echo "XML conversion completed for $dataset"
        if python3 "$json_to_csv_script_path" "$json_output_file" "$csv_output_file"; then
          echo "Json conversion completed for $dataset"
          echo "$RETRY_DELAY wait time between downloads"
          sleep "$RETRY_DELAY"
          break
        else
          echo "Error: JSON conversion failed for dataset: $dataset."
          exit 1
        fi
      else
        echo "Error: XML conversion failed for dataset: $dataset."
        exit 1
      fi
    else
      EXIT_CODE=$? # Capture the exit code of curl
      echo "Curl failed for $dataset on attempt $i with exit code: $EXIT_CODE."
      if [ $i -le $MAX_RETRIES ]; then
        echo "Retrying in $RETRY_DELAY seconds..."
        sleep "$RETRY_DELAY"
      else
        echo "Max retries reached. Curl failed permanently."
        exit 1 # Exit with an error status
      fi
    fi
    echo "$RETRY_DELAY wait time between downloads"
    sleep "$RETRY_DELAY"
  done
}

function download_datasets_for_country() {
  if [ -z "$1" ]; then
    echo "Usage: download_datasets_for_country <country_name> [<dataset_ids>] [<WORKING_DIR>]"
    echo "  <country_name>: The full name of the country (e.g., cotedivoire, kenya, rwanda, egypt)."
    echo "  <dataset_ids> (optional): A comma-separated list of dataset IDs to download. (e.g., 'dlrrjxg,egdxgkd,emxkej,fwjfdnc,gxbucsd')"
    echo "  <WORKING_DIR> (optional): The directory to store the downloaded files. relative path from data  (e.g., /data/statvar_imports/opendataforafrica/kenya_census/input_files )"
    echo "                          If not provided, a directory 'input_files' will be created in the current working directory."
    echo "No country specified. Exiting"
    exit 1
  fi

  COUNTRY="${1//\'/}"
  SELECTED_DATASETS_STRING="${2//\'/}"
  WORKING_DIR="${3//\'/}"

  if [ -z "$WORKING_DIR" ]; then
    WORKING_DIR=$(pwd)/"input_files"
  fi

  mkdir -p "$WORKING_DIR"

  if [ -n "$SELECTED_DATASETS_STRING" ]; then
    IFS=',' read -ra SELECTED_DATASETS <<< "$SELECTED_DATASETS_STRING"
    for dataset in "${SELECTED_DATASETS[@]}"; do
      download_and_convert_dataset "$dataset"
    done
  else
    download_key_families
    local script_path="../../../util/xml_to_json.py"
    python3 "$script_path" "$WORKING_DIR/key_family.xml" "$WORKING_DIR/key_family.json"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to convert key_family.xml to key_family.json."
        exit 1
    fi

    extract_key_families
    
    if [ -f "$WORKING_DIR/key_family.xml" ] && [ -f "$WORKING_DIR/key_family.json" ]; then
      for dataset in "${DATASETS[@]}"; do
        download_and_convert_dataset "$dataset"
      done
      rm -f "$WORKING_DIR/key_family.xml" "$WORKING_DIR/key_family.json"
    else
      echo "Error: Key family files (XML or JSON) not found after processing."
      exit 1
    fi
  fi
}

# Call the main function with the provided arguments
download_datasets_for_country "$1" "$2" "$3"
