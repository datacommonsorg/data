#!/bin/bash

DEST="gazetteer/raw_data_2025"
mkdir -p $DEST
BASE_URL="https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer"

# Updated list to fix 404 errors
FILES=(
    "zcta_national" 
    "unsd_national" 
    "tracts_national" 
    "ua_national" 
    "sldu_national" 
    "place_national" 
    "sldl_national" 
    "sdadm_national" 
    "scsd_national" 
    "cousubs_national" 
    "elsd_national" 
    "counties_national" 
    "aiannhrt_national" 
    "119CDs_national"     # Updated from 116CDs
    "aiannh_national"      # Primary Tribal file
    "cbsa_national"
)

echo "--- Downloading 2025 Gazetteer Files ---"
for file in "${FILES[@]}"; do
    ZIP="2025_Gaz_${file}.zip"
    echo -n "Fetching $ZIP... "
    curl -L -f -s -o "$DEST/$ZIP" "$BASE_URL/$ZIP"
    
    if [ $? -eq 0 ] && [ -f "$DEST/$ZIP" ]; then
        if unzip -t "$DEST/$ZIP" > /dev/null 2>&1; then
            unzip -o -q "$DEST/$ZIP" -d "$DEST/"
            echo "Done."
            rm "$DEST/$ZIP"
        else
            echo "FAILED: Invalid zip."
            rm "$DEST/$ZIP"
        fi
    else
        echo "FAILED: 404. ($BASE_URL/$ZIP)"
    fi
done

echo "--- Download Complete ---"
ls -l $DEST/