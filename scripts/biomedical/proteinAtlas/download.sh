#!/bin/bash

# URLs of the files to download
URL1="https://www.proteinatlas.org/download/proteinatlas.tsv.zip"
URL2="https://v22.proteinatlas.org/download/normal_tissue.tsv.zip"

# Extract filename from URL
FILE1=$(basename "$URL1")
FILE2=$(basename "$URL2")

# Download the files, overwriting existing files if they exist
echo "Downloading $URL1..."
curl -o "$FILE1" "$URL1"

echo "Downloading $URL2..."
curl -o "$FILE2" "$URL2"

# Check if downloads were successful
if [ -f "$FILE1" ] && [ -f "$FILE2" ]; then
  echo "Downloads successful."

  # Unzip the files, overwriting existing files without prompting
  echo "Unzipping $FILE1..."
  unzip -o "$FILE1"

  echo "Unzipping $FILE2..."
  unzip -o "$FILE2"

  # Clean up zip files (optional)
  echo "Cleaning up zip files..."
  rm "$FILE1" "$FILE2"

  echo "Script completed."
else
  echo "Error: One or both downloads failed."
  if [ ! -f "$FILE1" ]; then
    echo "Download of $URL1 failed."
  fi
  if [ ! -f "$FILE2" ]; then
    echo "Download of $URL2 failed."
  fi
  exit 1
fi

exit 0