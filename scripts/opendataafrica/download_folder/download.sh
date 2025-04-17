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
OUTPUT_XML_JSON_DIR=$(pwd)/"$2/$1/openafrica_xml_folder"
# OUTPUT_XML_JSON_DIR="$2/$1/openafrica_xml_folder"
OUTPUT_CSV_DIR=""
DATASETS=()
SELECTED_DATASETS=()

function download_key_families() {
  echo "Downloading key family for country = $COUNTRY"
  if [ -f "$OUTPUT_XML_JSON_DIR/key_family.xml" ] && [ $(stat -c%s "$OUTPUT_XML_JSON_DIR/key_family.xml") -gt 0 ]; then
    echo "File $OUTPUT_XML_JSON_DIR/key_family.xml already exists. Skipping download."
    return
  fi
  curl -s --location "https://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx" \
    --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9;v=b3;q=0.7' \
    --header 'Accept-Encoding: gzip, deflate, br, zstd' \
    --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
    --output "$OUTPUT_XML_JSON_DIR/key_family.xml" \
    --compressed
}

function extract_key_families() {
  DATASETS=($(jq -r '."message:Structure"."message:KeyFamilies".KeyFamily.[]."@id"' "$OUTPUT_XML_JSON_DIR/key_family.json"))
}

function download_dataset() {
  local dataset="$1"
  echo "Downloading ${dataset} to file $OUTPUT_XML_JSON_DIR/${dataset}.xml"
  if [ -f "$OUTPUT_XML_JSON_DIR/${dataset}.xml" ] && [ $(stat -c%s "$OUTPUT_XML_JSON_DIR/${dataset}.xml") -gt 0 ]; then
    echo "File $OUTPUT_XML_JSON_DIR/${dataset}.xml exists, skipping download."
    return
  fi
  curl -s --location "http://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx/data/${dataset}" \
    --header 'Accept: text/html,application/xhtml+xml,application/xml' \
    --header 'Accept-Encoding: gzip, deflate, br, zstd' \
    --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
    --output "$OUTPUT_XML_JSON_DIR/${dataset}.xml" \
    --compressed
}

function xml_to_json() {
  local xml_file="$1"
  local json_file="$2"
    local script_path="../../../util/xml_to_json.py"
  python3 "$script_path" "$xml_file" "$json_file"
  # python3 xml_to_json.py --input_xml="$xml_file" --output_json="$json_file"
}

function download_selected_DATASETS() {
  for dataset in "${SELECTED_DATASETS[@]}"; do
    download_dataset "$dataset"
    if [ $? -eq 0 ]; then
      local json_output_file="$OUTPUT_XML_JSON_DIR/${dataset}.json"
      local csv_output_file="$OUTPUT_CSV_DIR/${dataset}.csv"
      local script_path="../../../util/xml_to_json.py"
      if python3 "$script_path"  "$OUTPUT_XML_JSON_DIR/${dataset}.xml" "$json_output_file"; then
        echo "Successfully converted ${dataset}.xml to ${dataset}.json"
        local script_path1="json_to_csv.py"

        if python3 "$script_path1"  "$OUTPUT_XML_JSON_DIR" "$OUTPUT_CSV_DIR"; then
          echo "Successfully converted JSON files in $OUTPUT_XML_JSON_DIR to CSV files in $OUTPUT_CSV_DIR"
        else
          echo "Error: Failed to convert JSON files to CSV files."
        fi
      else
        echo "Error: Failed to convert ${dataset}.xml to ${dataset}.json"
      fi
    else
      echo "Error: Failed to download dataset $dataset"
    fi
  done
}
function download_all_DATASETS() {
  local last_download_status=0
  local xml_to_json_script_path="../../../util/xml_to_json.py"
  local json_to_csv_script_path="json_to_csv.py"

  for dataset in "${DATASETS[@]}"; do
    download_dataset "$dataset"
    local download_status=$?
    last_download_status=$download_status # Update the last status

    if [ $download_status -eq 0 ]; then
      local xml_output_file="$OUTPUT_XML_JSON_DIR/${dataset}.xml"
      local json_output_file="$OUTPUT_XML_JSON_DIR/${dataset}.json"
      local csv_output_file="$OUTPUT_CSV_DIR/${dataset}.csv"

      if python3 "$xml_to_json_script_path" "$xml_output_file" "$json_output_file"; then
        echo "Successfully converted ${dataset}.xml to ${dataset}.json"
        if python3 "$json_to_csv_script_path" "$OUTPUT_XML_JSON_DIR" "$OUTPUT_CSV_DIR"; then
          echo "Successfully converted JSON files in $OUTPUT_XML_JSON_DIR to CSV files in $OUTPUT_CSV_DIR"
        else
          echo "Error: Failed to convert JSON files in $OUTPUT_XML_JSON_DIR to CSV files in $OUTPUT_CSV_DIR."
        fi
      else
        echo "Error: Failed to convert ${dataset}.xml to ${dataset}.json"
      fi
    else
      echo "Error: Failed to download dataset $dataset (curl exit code: $download_status)"
    fi
  done
  return $last_download_status
}


function download_DATASETS_for_country() {
  if [ -z "$1" ]; then
    echo "Usage: download_DATASETS_for_country <country_name>"
    echo "  <country_name>: The full name of the country (e.g., cotedivoire)."
    echo "No country specified. Exiting"
    exit 1
  fi
  COUNTRY="$1"

  if [ -z "$2" ]; then
    echo "  <output_folder>: The path to the directory where the downloaded CSV files will be stored ."
    echo "No output CSV folder specified. Exiting"
    exit 1
  fi
  OUTPUT_CSV_DIR="$2"

  echo "Making output directory for XML/JSON: $OUTPUT_XML_JSON_DIR"
  mkdir -p "$OUTPUT_XML_JSON_DIR"

  echo "Making output directory for CSV: $OUTPUT_CSV_DIR"
  mkdir -p "$OUTPUT_CSV_DIR"

  download_key_families
  if [ -f "$OUTPUT_XML_JSON_DIR/key_family.xml" ]; then
    xml_to_json "$OUTPUT_XML_JSON_DIR/key_family.xml" "$OUTPUT_XML_JSON_DIR/key_family.json"
    if [ -f "$OUTPUT_XML_JSON_DIR/key_family.json" ]; then
      extract_key_families
      echo "Available DATASETS: ${DATASETS[@]}"
      echo "Total available DATASETS: ${#DATASETS[@]}"

      # Check if a list of DATASETS is provided as the third argument
      if [ -n "$3" ]; then
        echo "Selected DATASETS provided: $3"
        IFS=',' read -ra SELECTED_DATASETS <<< "$3"
        echo "DATASETS to download: ${SELECTED_DATASETS[@]}"
        download_selected_DATASETS
      else
        echo "No specific DATASETS provided. Downloading all DATASETS."
        download_all_DATASETS
      fi
    else
      echo "Error: key_family.xml not found. Download failed. (Path: $OUTPUT_XML_JSON_DIR/key_family.xml)"
      exit 1
    fi
  else
    echo "Error: key_family.json not found. Conversion failed. (Path: $OUTPUT_XML_JSON_DIR/key_family.json)"
    exit 1
  fi
}

# Call the main function with the provided arguments
download_DATASETS_for_country "$1" "$2" "$3"
