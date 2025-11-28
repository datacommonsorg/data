#!/bin/bash

# =================================================================
# CONFIGURATION SECTION - PLEASE EDIT THESE PATHS
# =================================================================

# Define the directory containing the input files (as requested, this is 'source_files')
INPUT_DIR="./input_files"

# Set the paths for the arguments that are common to all runs.
# !!! IMPORTANT: Replace these placeholder values with your actual file paths. !!!
PV_MAP_FILE="student_faculty_ratio_pvmap.csv"
CONFIG_FILE="student_faculty_ratio_metadata.csv"
OUTPUT_DIR="processed_output" # Make sure this directory exists!

# The fixed argument for the existing statvar MCF file
EXISTING_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

# The name of the Python script
PYTHON_SCRIPT="../../../tools/statvar_importer/stat_var_processor.py"

# =================================================================
# EXECUTION LOGIC
# =================================================================

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if the input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' not found."
    exit 1
fi

echo "Starting parallel processing of files in $INPUT_DIR..."
JOB_COUNT=0

# Loop through all files in the source_files directory
for input_file in "$INPUT_DIR"/*; do
    # Check if the item is a regular file before processing
    if [ -f "$input_file" ]; then
        
        # 1. Determine the output path for the current file
        # We derive the output filename from the input filename (e.g., file.csv -> file.mcf)
        base_name=$(basename "$input_file")
        file_extension="${base_name##*.}"
        filename_only="${base_name%.*}"
        
        output_file="$OUTPUT_DIR/${filename_only}"
        
        echo "Launching job for: $input_file (Output: $output_file)"
        
        # 2. Run the Python script in the background using the '&' operator
        python3 "$PYTHON_SCRIPT" \
            --input_data="$input_file" \
            --pv_map="$PV_MAP_FILE" \
            --config_file="$CONFIG_FILE" \
            --existing_statvar_mcf="$EXISTING_MCF" \
            --output_path="$output_file" &
        
        JOB_COUNT=$((JOB_COUNT + 1))
    fi
done

echo "---"
echo "Launched $JOB_COUNT jobs in the background."
echo "Waiting for all parallel processing jobs to complete..."

# 3. Use 'wait' to pause the script until all background processes have finished
wait

echo "All parallel processing jobs are complete. Output files are in $OUTPUT_DIR"