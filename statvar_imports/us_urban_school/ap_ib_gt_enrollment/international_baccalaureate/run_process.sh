#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the script's directory to ensure relative paths work correctly.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Default to not downloading
DOWNLOAD=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --download) DOWNLOAD=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Function to process each downloaded data file.
process_files() {
    # Create the output directory if it doesn't exist.
    mkdir -p output_files

    # Loop through all International Baccalaureate Enrollment files in the input directory.
    for input_file in input_files/*_IB_Enrollment.*; do
        # Check if any file exists to avoid errors when no files are found.
        [ -e "$input_file" ] || continue

        echo "Processing file: $input_file"

        # Extract the year from the filename (e.g., "2014" from "2014_IB_Enrollment.xlsx").
        filename=$(basename "$input_file")
        year=$(echo "$filename" | cut -d'_' -f1)

        # Define the output path based on the year.
        output_path="output_files/output_${year}_ib"

        # Construct the command from the manifest.
        CMD_ARRAY=(python3 ../../../tools/statvar_importer/stat_var_processor.py \
            --input_data="${input_file}" \
            --pv_map=../config/ib_enrollment_pvmap.csv \
            --config_file=../config/common_metadata.csv \
            --output_path="${output_path}" \
            --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf)
        # Print and execute the command.
        echo "Executing command for year ${year}:"
        printf "%q " "${CMD_ARRAY[@]}"; echo
        "${CMD_ARRAY[@]}"
        echo "--- Finished processing for year ${year} ---"
    done
}

if [ "$DOWNLOAD" = true ]; then
    echo "--- Starting download of IB data ---"
    python3 ../download_ap_ib_gt.py --ib
    python3 ../download_2015_16.py --ib
    echo "--- Download complete ---"
fi

echo "--- Starting processing of files ---"
process_files
echo "--- All processing complete ---"
