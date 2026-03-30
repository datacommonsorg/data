#!/bin/bash

# --- Variables ---
BUCKET=${BUCKET:-"unresolved_mcf"}
CYCLE=${CYCLE:-"00"}
DATE_STAMP=$(date +%Y%m%d)
FILE_NAME="gfs.t${CYCLE}z.pgrb2.0p25.f000"
URL="https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.${DATE_STAMP}/${CYCLE}/atmos/${FILE_NAME}"

echo "Starting pipeline for ${DATE_STAMP} cycle ${CYCLE}..."

# Helper to use sudo only if we aren't already root
SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

# --- Updated 1. Runtime Installation ---
# Added libaec-dev to the list
$SUDO apt-get update && $SUDO apt-get install -y \
    build-essential gfortran cmake git libg2c-dev libaec-dev curl

# Clone and build
rm -rf wgrib2 
git clone --depth 1 https://github.com/NOAA-EMC/wgrib2.git
cd wgrib2
mkdir build && cd build
# We add a flag to tell CMake where to find libraries if it struggles
cmake .. -DCMAKE_INSTALL_PREFIX=./install
make -j$(nproc)
make install

# --- the binary path---
WGRIB2_BIN="$(pwd)/install/bin/wgrib2"

# Move back to start directory
cd ../..

# --- 2. Download GFS Data ---
echo "Downloading GFS data..."
curl -L -o "./${FILE_NAME}" "$URL"

# --- 3. Convert GRIB2 to CSV ---
echo "Converting to CSV..."
# Call the binary using the confirmed install path
$WGRIB2_BIN "./${FILE_NAME}" -csv "./${FILE_NAME}.csv"

# --- 4. Upload to GCS ---
echo "Uploading to gs://${BUCKET}/..."
gsutil cp "./${FILE_NAME}.csv" "gs://${BUCKET}/noaa_gfs/${DATE_STAMP}/input_files/${FILE_NAME}.csv"

# --- 5. Run StatVar Processing ---
echo "Running StatVar processing and streaming to GCS..."
python3 custom_statvar_processor.py \
    --bucket_name="${BUCKET}" \
    --input_local="./${FILE_NAME}.csv" \
    --output_blob_name="noaa_gfs/${DATE_STAMP}/output/noaa_gfs_output.csv"

# --- 6. Upload TMCF to GCS ---
echo "Uploading TMCF to gs://${BUCKET}/noaa_gfs/${DATE_STAMP}/output/..."
gsutil cp "gs://${BUCKET}/noaa_gfs/noaa_gfs_output.tmcf" "gs://${BUCKET}/noaa_gfs/${DATE_STAMP}/output/"

echo "Pipeline complete."
