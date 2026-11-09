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

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

tmp="source_data_tmp"
files="input_data"
retries=3
wait=5
download_url="https://bulks-faostat.fao.org/production/Exchange_rate_E_All_Data_(Normalized).zip"
output_file="Exchange_rate_E_All_Data_(Normalized).zip"

mkdir -p "$tmp"
mkdir -p "$files"

cd "$tmp" || { echo "Failed to change directory to $tmp"; exit 1; }

download_with_retry() {
  url="$1"
  output="$2"
  attempt=1
  while [[ $attempt -le "$retries" ]]; do
    echo "Attempt $attempt: Downloading '$url' to '$output'..."
    if curl -f -L "$url" -o "$output"; then
      echo "Download successful."
      return 0
    else
      echo "Download failed (attempt $attempt). Waiting $wait seconds before retrying..."
      sleep "$wait"
      attempt=$((attempt + 1))
    fi
  done
  echo "Failed to download '$url' after $retries attempts."
  return 1
}

if download_with_retry "$download_url" "$output_file"; then
  unzip -o "$output_file" -d Exchange_rate_E_All_Data
  cd ..
  if [ -f "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data_(Normalized).csv" ]; then
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data_(Normalized).csv" "$files/Exchange_rate_E_All_Data_(Normalized).csv"
  else
    echo "Error: Unzipped file '$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data_(Normalized).csv' not found."
    exit 1
  fi
else
  echo "Skipping unzip and move operations due to download failure."
  exit 1
fi

rm -rf "$tmp"
echo "Download script finished successfully."
exit 0
