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

    declare -A processed_years

    # Loop through all AP Enrollment files in the input directory to identify unique years
    for input_file in input_files/*_AP_Enrollment.*; do
        # Check if any file exists to avoid errors when no files are found.
        [ -e "$input_file" ] || continue

        filename=$(basename "$input_file")
        year=$(echo "$filename" | cut -d'_' -f1)
        extension="${filename##*.}"

        # Determine expected extension based on year
        expected_extension=""
        if [[ "$year" == "2010" || "$year" == "2012" || "$year" == "2014" ]]; then
            expected_extension="xlsx"
        else
            expected_extension="csv"
        fi

        # Skip if the extension does not match the expected one
        if [[ "$extension" != "$expected_extension" ]]; then
            echo "Skipping $input_file: Expected .$expected_extension, but found .$extension."
            continue
        fi

        # If this year hasn't been processed yet, process it
        if [[ -z ${processed_years[$year]} ]]; then
            processed_years[$year]=true
            echo "Processing year: $year"

            # Define the glob pattern for input files for this year
            input_data_glob="input_files/${year}_AP_Enrollment_*.${expected_extension}"

            # Define the output path based on the year.
            output_path="output_files/output_${year}_ap"

            # Construct the command for the current year
            CMD_ARRAY=(python3 ../../../tools/statvar_importer/stat_var_processor.py \
                --input_data="${input_data_glob}" \
                --pv_map=../config/ap_enrollment_pvmap.csv \
                --config_file=../config/common_metadata.csv \
                --output_path="${output_path}" \
                --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf)
            # Print and execute the command.
            echo "Executing command for year ${year}:"
            printf "%q " "${CMD_ARRAY[@]}"; echo
            "${CMD_ARRAY[@]}"
            echo "--- Finished processing for year ${year} ---"
        fi
    done
}

if [ "$DOWNLOAD" = true ]; then
    echo "--- Starting download of AP data ---"
    python3 ../download_ap_ib_gt.py --ap
    python3 ../download_2015_16.py --ap
    echo "--- Download complete ---"
fi

echo "--- Starting processing of files ---"
process_files
echo "--- All processing complete ---"

