#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the script's directory to ensure relative paths work correctly.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Always download data
echo "--- Starting download of GT data ---"
python3 ../download_ap_ib_gt.py --gt
python3 ../download_2015_16.py --gt
echo "--- Download complete ---"

# Function to process each downloaded data file.
process_files() {
    # Create the output directory if it doesn't exist.
    mkdir -p output_files

    # Loop through all Gifted and Talented Enrollment files in the input directory.
    for input_file in input_files/*_GT_Enrollment.*; do
        # Check if any file exists to avoid errors when no files are found.
        [ -e "$input_file" ] || continue

        echo "Processing file: $input_file"

        # Extract the year from the filename (e.g., "2014" from "2014_GT_Enrollment.xlsx").
        filename=$(basename "$input_file")
        year=$(echo "$filename" | cut -d'_' -f1)

        # Define the output path based on the year.
        output_path="output_files/output_${year}_gt"

        # Construct the command from the manifest.
        CMD="python3 ../../../../../data/tools/statvar_importer/stat_var_processor.py"
        CMD+=" --input_data=\"${input_file}\""
        CMD+=" --pv_map=../config/gt_enrollment_pvmap.csv"
        CMD+=" --config_file=../config/common_metadata.csv"
        CMD+=" --output_path=\"${output_path}\""
        CMD+=" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

        # Print and execute the command.
        echo "Executing command for year ${year}:"
        echo "$CMD"
        eval "$CMD"
        echo "--- Finished processing for year ${year} ---"
    done
}

echo "--- Starting processing of files ---"
process_files
echo "--- All processing complete ---"
