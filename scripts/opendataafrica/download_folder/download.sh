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

COUNTRY=""
DATASETS=()
SELECTED_DATASETS=()

function download_key_families() {
  echo "Downloading key family for country = $COUNTRY"
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
  # local dataset="$1"
  echo "Downloading ${dataset} to file $WORKING_DIR/${dataset}.xml"
  if [ -f "$WORKING_DIR/${dataset}.xml" ] && [ $(stat -c%s "$WORKING_DIR/${dataset}.xml") -gt 0 ]; then
    echo "File $WORKING_DIR/${dataset}.xml exists, skipping download."
  else
    curl -s --location "http://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx/data/${dataset}" \
      --header 'Accept: text/html,application/xhtml+xml,application/xml' \
      --header 'Accept-Encoding: gzip, deflate, br, zstd' \
      --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
      --output "$WORKING_DIR/${dataset}.xml" \
      --compressed
    if [ $? -ne 0 ]; then
      echo "Error: Failed to download dataset $dataset"
      return 1
    fi
  fi

  local json_output_file="$WORKING_DIR/${dataset}.json"
  local csv_output_file="$WORKING_DIR/${dataset}.csv"
  local xml_to_json_script_path="../../../util/xml_to_json.py"
  local json_to_csv_script_path="json_to_csv.py"

  if python3 "$xml_to_json_script_path" "$WORKING_DIR/${dataset}.xml" "$json_output_file"; then
    echo "Successfully converted ${dataset}.xml to ${dataset}.json"
    if python3 "$json_to_csv_script_path" "$WORKING_DIR" "$WORKING_DIR"; then
      echo "Successfully converted JSON files in $WORKING_DIR to CSV files in $WORKING_DIR"
      rm -f "$WORKING_DIR/${dataset}.xml"
      echo "Removed XML file: $WORKING_DIR/${dataset}.xml"
      rm -f "$WORKING_DIR/${dataset}.json"
        # rm -f "$WORKING_DIR/${dataset}.json"
      echo "Removed JSON file: $WORKING_DIR/${dataset}.json"
      return 0
    else
      echo "Error: Failed to convert JSON files to CSV files."
      return 1
    fi
  else
    echo "Error: Failed to convert ${dataset}.xml to ${dataset}.json"
    return 1
  fi
}

function download_datasets_for_country() {
  if [ -z "$1" ]; then
    echo "Usage: download_datasets_for_country <country_name> [<dataset_ids>] [<WORKING_DIR>]"
    echo "  <country_name>: The full name of the country (e.g., cotedivoire)."
    echo "  <dataset_ids> (optional): A comma-separated list of dataset IDs to download."
    echo "  <WORKING_DIR> (optional): The directory to store the downloaded files."
    echo "                            If not provided, a directory 'input_files' will be created in the current working directory."
    echo "No country specified. Exiting"
    exit 1
  fi
  COUNTRY="$1"
  SELECTED_DATASETS_STRING="$2"
  WORKING_DIR="$3"

  if [ -z "$WORKING_DIR" ]; then
    WORKING_DIR=$(pwd)/"input_files"
  fi

  echo "Making output directory: $WORKING_DIR"
  mkdir -p "$WORKING_DIR"

  if [ -n "$SELECTED_DATASETS_STRING" ]; then
    echo "Selected DATASETS provided: $SELECTED_DATASETS_STRING"
    IFS=',' read -ra SELECTED_DATASETS <<< "$SELECTED_DATASETS_STRING"
    echo "Downloading selected DATASETS: ${SELECTED_DATASETS[@]}"
    for dataset in "${SELECTED_DATASETS[@]}"; do
      download_and_convert_dataset "$dataset"
    done

    echo "Completed processing selected datasets. Removing JSON files."
    for dataset in "${SELECTED_DATASETS[@]}"; do
      rm -f "$WORKING_DIR/${dataset}.json"
      echo "Removed JSON file: $WORKING_DIR/${dataset}.json"
    done
  else
    download_key_families
    local script_path="../../../util/xml_to_json.py"
    python3 "$script_path" "$WORKING_DIR/key_family.xml" "$WORKING_DIR/key_family.json"
    extract_key_families
    if [ -f "$WORKING_DIR/key_family.xml" ]; then
      
      if [ -f "$WORKING_DIR/key_family.json" ]; then
        echo "Available DATASETS: ${DATASETS[@]}"
        echo "Total available DATASETS: ${#DATASETS[@]}"
        echo "No specific DATASETS provided. Only key family information downloaded."
        for dataset in "${DATASETS[@]}"; do
          download_and_convert_dataset "$dataset"
        done
        echo "Removing key family XML and JSON files."
        rm -f "$WORKING_DIR/key_family.xml" "$WORKING_DIR/key_family.json"
        echo "Removed: $WORKING_DIR/key_family.xml and $WORKING_DIR/key_family.json"
        
      else
        echo "Error: key_family.json not found. Conversion failed. (Path: $WORKING_DIR/key_family.json)"
        exit 1
      fi
    else
      echo "Error: key_family.xml not found. Download failed. (Path: $WORKING_DIR/key_family.xml)"
      exit 1
    fi
  fi
}

# Call the main function with the provided arguments
download_datasets_for_country "$1" "$2" "$3"
