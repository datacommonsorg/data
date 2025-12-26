#!/bin/bash
# Script to download all five WHO COVID-19 datasets

# Set path variable for cleaner reading
PYTHON_UTIL="../../util/download_util_script.py"
OUTPUT_DIR="input_files/"
mkdir -p "$OUTPUT_DIR"

# 1. Archived Vaccine Uptake (2021-2023)
python3 "$PYTHON_UTIL" --download_url=https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/COV_VAC_UPTAKE_2021_2023.csv --output_folder="$OUTPUT_DIR"

# 2. Current Vaccine Uptake (2024)
python3 "$PYTHON_UTIL" --download_url=https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/COV_VAC_UPTAKE_2024.csv --output_folder="$OUTPUT_DIR"

# 3. Global Daily Data
python3 "$PYTHON_UTIL" --download_url=https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-daily-data.csv --output_folder="$OUTPUT_DIR"

# 4. Global Hospitalization/ICU Data
python3 "$PYTHON_UTIL" --download_url=https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-hosp-icu-data.csv --output_folder="$OUTPUT_DIR"

# 5. Monthly Deaths by Age Data
python3 "$PYTHON_UTIL" --download_url=https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-monthly-death-by-age-data.csv --output_folder="$OUTPUT_DIR"

echo "All 5 download jobs complete."

