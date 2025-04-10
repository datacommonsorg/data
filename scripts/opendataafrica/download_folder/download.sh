#!/bin/bash

# Instructions to run the script
# 1. Copy this script and xml_to_json.py to a directory
# 2. Create a python virtual environment and install required packages
#   python3 -m venv .env
#   source .env/bin/activate
#   pip install -r requirements.txt absl-py
# 3. Make the script executable: chmod +x opendata_africa_download_data.sh
# 4. Run the script: ./opendata_africa_download_data.sh <country_name> <output_csv_folder>
#   e.g. ./opendata_africa_download_data.sh rwanda csv_output
#   Output files will be stored in a directory named 'openafrica_xml_folder' for XML and JSON,
#   and the specified <output_csv_folder> for CSV files.

COUNTRY=""
OUTPUT_XML_JSON_DIR=$(pwd)/openafrica_xml_folder
OUTPUT_CSV_DIR=""
datasets=()

function download_key_families() {
  echo "Downloading key family for country = $COUNTRY"
  if [ -f "$OUTPUT_XML_JSON_DIR/key_family.xml" ] && [ $(stat -c%s "$OUTPUT_XML_JSON_DIR/key_family.xml") -gt 0 ]; then
    echo "File $OUTPUT_XML_JSON_DIR/key_family.xml already exists. Skipping download."
    return
  fi
  curl -s --location "https://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx" \
    --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
    --header 'Accept-Encoding: gzip, deflate, br, zstd' \
    --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
    --output "$OUTPUT_XML_JSON_DIR/key_family.xml" \
    --compressed
}

function extract_key_families() {
  datasets=($(jq -r '."message:Structure"."message:KeyFamilies".KeyFamily.[]."@id"' "$OUTPUT_XML_JSON_DIR/key_family.json"))
}

function download_dataset() {
  local dataset="$1"
  echo "Downloading ${dataset} to file $OUTPUT_XML_JSON_DIR/${dataset}.xml"
  if [ -f "$OUTPUT_XML_JSON_DIR/${dataset}.xml" ] && [ $(stat -c%s "$OUTPUT_XML_JSON_DIR/${dataset}.xml") -gt 0 ]; then
    echo "File $OUTPUT_XML_JSON_DIR/${dataset}.xml exists, skipping download."
    return
  fi
  curl -s --location "http://${COUNTRY}.opendataforafrica.org/api/1.0/sdmx/data/${dataset}" \
    --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
    --header 'Accept-Encoding: gzip, deflate, br, zstd' \
    --header 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
    --output "$OUTPUT_XML_JSON_DIR/${dataset}.xml" \
    --compressed
}

function xml_to_json() {
  local xml_file="$1"
  local json_file="$2"
  python3 xml_to_json.py --input_xml="$xml_file" --output_json="$json_file"
}

function download_all_datasets() {
  for dataset in "${datasets[@]}"; do
    download_dataset "$dataset"
    if [ $? -eq 0 ]; then
      local json_output_file="$OUTPUT_XML_JSON_DIR/${dataset}.json"
      local csv_output_file="$OUTPUT_CSV_DIR/${dataset}.csv"
      if python3 xml_to_json.py --input_xml="$OUTPUT_XML_JSON_DIR/${dataset}.xml" --output_json="$json_output_file"; then
        echo "Successfully converted ${dataset}.xml to ${dataset}.json"
        # Corrected call to json_to_csv.py with flags and output directory
        if python3 json_to_csv.py --input_json="$OUTPUT_XML_JSON_DIR" --output_csv="$OUTPUT_CSV_DIR"; then
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

function download_all_datasets_for_country() {
  if [ -z "$1" ]; then
    echo "No country specified. Exiting"
    exit 1
  fi
  COUNTRY="$1"

  if [ -z "$2" ]; then
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
      echo "Datasets = ${datasets[@]}"
      echo "Dataset length = ${#datasets[@]}"
      download_all_datasets
    else
      echo "Error: key_family.json not found. Conversion failed."
    fi
  else
    echo "Error: key_family.xml not found. Download failed."
  fi
}

download_all_datasets_for_country "$1" "$2"