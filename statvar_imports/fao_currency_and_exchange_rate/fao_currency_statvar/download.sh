#!/bin/bash

tmp="source_data_tmp" # where to store temporary artifacts
dest="source_data" # where to put the final files
files="input_files"
# Make directories
mkdir -p "$tmp"
mkdir -p "$dest"
mkdir -p "$files"
# Download data files
## Links copied from https://hazards.fema.gov/nri/data-resources
cd "$tmp"


curl -L https://bulks-faostat.fao.org/production/Exchange_rate_E_All_Data.zip -o Exchange_rate_E_All_Data.zip
unzip Exchange_rate_E_All_Data.zip -d Exchange_rate_E_All_Data

cd ..
# cd Exchange_rate_E_All_Data
mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data.csv" "$files"
mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_All_Data_NOFLAG.csv" "$dest"
mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_AreaCodes.csv" "$dest"
mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_Currencys.csv" "$dest"
mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_Elements.csv" "$dest"
mv "$tmp/Exchange_rate_E_All_Data/Exchange_rate_E_Flags.csv" "$dest"


# Clean up temporary artifacts
rm -rf "$tmp"
