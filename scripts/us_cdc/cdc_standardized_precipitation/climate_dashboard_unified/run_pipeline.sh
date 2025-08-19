#!/bin/bash
#
# This script creates a fully automated pipeline to download the raw climate data,
# process it, and prepare it for the Unified Climate Dashboard.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Get the directory of this script ---
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
PARENT_DIR=$(dirname "$SCRIPT_DIR")

echo "--- Starting Data Pipeline for Unified Climate Dashboard ---"

# --- Step 1: Download Raw Data ---
# The main download script and its config are in the parent directory.
# We will call it for each of the three climate indices.

echo "[1/4] Downloading Standardized Precipitation Index (SPI) data..."
python3 "${PARENT_DIR}/download_script.py" \
  --import_name=CDC_StandardizedPrecipitationIndex \
  --config_file="${PARENT_DIR}/import_configs.json"

echo "[2/4] Downloading Palmer Drought Severity Index (PDSI) data..."
python3 "${PARENT_DIR}/download_script.py" \
  --import_name=CDC_PalmerDroughtSeverityIndex \
  --config_file="${PARENT_DIR}/import_configs.json"

echo "[3/4] Downloading Standardized Precipitation Evapotranspiration Index (SPEI) data..."
python3 "${PARENT_DIR}/download_script.py" \
  --import_name=CDC_StandardizedPrecipitationEvapotranspirationIndex \
  --config_file="${PARENT_DIR}/import_configs.json"

echo "All raw data downloaded successfully."

# --- Step 2: Combine and Process Data ---
# This script is located in the same directory as the pipeline script.
echo "[4/4] Combining and processing all data into a unified Parquet file..."
python3 "${SCRIPT_DIR}/combine_data.py"

echo ""
echo "--- ✅ Pipeline Completed Successfully! ---"
echo ""
echo "The data is now ready for the dashboard."
echo "To launch the application, run the following command:"
echo ""
echo "streamlit run \"${SCRIPT_DIR}/app.py\""
echo ""
