#!/bin/bash

tmp="source_data_tmp" # where to store temporary artifacts
dest="source_data" # where to put the final files
files="input_data"
retries=3
wait=5 # seconds to wait between retries
download_url="https://bulks-faostat.fao.org/production/Exchange_rate_E_All_Data.zip"
output_file="Exchange_rate_E_All_Data.zip"

# Make directories
mkdir -p "$tmp"
mkdir -p "$dest"
mkdir -p "$files"

# Download data file with retry
cd "$tmp" || { echo "Failed to change directory to $tmp"; exit 1; } # Added error check for cd

download_with_retry() {
  url="$1"
  output="$2"
  attempt=1
  while [[ $attempt -le "$retries" ]]; do
    echo "Attempt $attempt: Downloading '$url' to '$output'..."
    curl -f -L "$url" -o "$output"
    if [ $? -eq 0 ]; then
      echo "Download successful."
      return 0 # Success
    else
      echo "Download failed (attempt $attempt). Waiting $wait seconds before retrying..."
      sleep "$wait"
      attempt=$((attempt + 1))
    fi
  done
  echo "Failed to download '$url' after $retries attempts."
  return 1 # Failure
}

if download_with_retry "$download_url" "$output_file"; then
  unzip "$output_file" -d Exchange_rate_E_All_Data
  cd ..
  if [ -d "$tmp/Exchange_rate_E_All_Data" ]; then
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data.csv" "$files"
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data_NOFLAG.csv" "$dest"
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_AreaCodes.csv" "$dest"
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_Currencys.csv" "$dest"
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_Elements.csv" "$dest"
    mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_Flags.csv" "$dest"
  else
    echo "Error: Unzipped directory '$tmp/Exchange_rate_E_All_Data' not found."
    exit 1
  fi
else
  echo "Skipping unzip and move operations due to download failure."
  exit 1
fi

# Clean up temporary artifacts
rm -rf "$tmp" || { echo "Failed to remove temporary directory $tmp"; exit 1; }

echo "Script finished successfully."
exit 0
