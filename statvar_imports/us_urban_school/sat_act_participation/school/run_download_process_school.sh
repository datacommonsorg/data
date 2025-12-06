#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the script's directory to ensure relative paths work correctly.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Run the Python download script to fetch the latest files.
python3 download_schoollevel.py --data_type=sat_act
echo "--- Download complete ---"
echo ""

# Function to process each downloaded data file.
process_files() {
    # Create the output directory if it doesn't exist.
    mkdir -p output_files_school

    # Loop through all SAT/ACT participation files in the input directory.
    for input_file in input_files_school/*_SAT_ACT_Participation.*; do
        # Check if any file exists to avoid errors when no files are found.
        [ -e "$input_file" ] || continue

        echo "Processing file: $input_file"

        # Extract the year from the filename (e.g., "2012" from "2012_SAT_ACT_Participation.xlsx").
        filename=$(basename "$input_file")
        year=$(echo "$filename" | cut -d'_' -f1)

        # Define the output path based on the year.
        output_path="output_files_school/output_${year}"

        # Construct the command from the manifest.
        CMD="python3 ../../../../tools/statvar_importer/stat_var_processor.py \
            --input_data=${input_file} \
            --pv_map=config/sat_act_participation_college_pvmap.csv \
            --config_file=config/sat_act_participation_college_metadata.csv \
            --output_path=${output_path} \
            --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

        # Print and execute the command.
        echo "Executing command for year ${year}:"
        echo "$CMD"
        eval "$CMD"
        echo "--- Finished processing for year ${year} ---"
    done
    echo "--- All files processed ---"
}

# Run the processing function.
process_files