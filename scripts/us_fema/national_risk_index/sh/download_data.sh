tmp="source_data_tmp" # where to store temporary artifacts
dest="source_data" # where to put the final files

# Make directories
mkdir "$tmp"
mkdir "$dest"

# Download data files
## Links copied from https://hazards.fema.gov/nri/data-resources
cd "$tmp"

## County-level data
## Zip includes data a copy of the data dictionary
### Double slash after DataDownload is intentional
curl -L https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_Counties/NRI_Table_Counties.zip -o NRI_Table_Counties.zip
unzip NRI_Table_Counties.zip -d NRI_Table_Counties

## Tract-level data
## Not used in the import currently, and very large file, so leaving commands
## for reference
#curl -L https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_Tracts/NRI_Table_CensusTracts.zip -o "$tmp/NRI_Table_CensusTracts.zip"
#mkdir "$tmp/tracts_unzipped"
#unzip NRI_Table_Counties.zip

# Move files to final destination
cd ..
mv "$tmp/NRI_Table_Counties/NRIDataDictionary.csv" "$dest"
mv "$tmp/NRI_Table_Counties/NRI_Table_Counties.csv" "$dest"

# Clean up temporary artifacts
rm -rf "$tmp"
