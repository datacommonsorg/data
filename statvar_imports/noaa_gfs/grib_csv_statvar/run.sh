#!/bin/bash

# Helper function for error checking
check_fail() {
    if [ $? -ne 0 ]; then
        echo "ERROR: $1" >&2
        exit 1
    fi
}

# --- Variables ---
BUCKET=${BUCKET:-"unresolved_mcf"}
CYCLE=${CYCLE:-"00"}
FHOUR=${FHOUR:-"000"}
DATE_STAMP=$(date +%Y%m%d)
FILE_NAME="gfs.t${CYCLE}z.pgrb2.0p25.f${FHOUR}"
URL="https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.${DATE_STAMP}/${CYCLE}/atmos/${FILE_NAME}"

echo "Starting pipeline for ${DATE_STAMP} cycle ${CYCLE} hour ${FHOUR}..."

# --- 1. Download GFS Data ---
echo "Downloading GFS data..."
curl -L -f -o "./${FILE_NAME}" "$URL"
check_fail "Failed to download ${URL}"

# --- 2. Convert GRIB to CSV ---
echo "Converting to CSV..."
python3 grib_to_csv.py \
    --input_file="./${FILE_NAME}" \
    --output_file="./${FILE_NAME}.csv"
check_fail "GRIB conversion failed for ${FILE_NAME}"

# --- 3. Upload to GCS ---
echo "Uploading to gs://${BUCKET}/..."
gsutil cp "./${FILE_NAME}.csv" "gs://${BUCKET}/noaa_gfs/${DATE_STAMP}/input_files/${FILE_NAME}.csv"
check_fail "Failed to upload CSV to GCS"

# --- 4. Run StatVar Processing ---
echo "Running StatVar processing and streaming to GCS..."
python3 custom_statvar_processor.py \
    --bucket_name="${BUCKET}" \
    --input_local="./${FILE_NAME}.csv" \
    --forecast_hour="${FHOUR}" \
    --output_blob_name="noaa_gfs/output/noaa_gfs_output_${DATE_STAMP}.csv"
check_fail "StatVar processing failed for ${FILE_NAME}"

echo "Pipeline complete."
