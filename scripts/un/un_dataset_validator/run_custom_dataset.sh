#!/bin/bash

# Simple wrapper script to run validations on a custom dataset

if [ "$#" -ne 4 ]; then
    echo "Usage: ./run_custom_dataset.sh <dataset_name> <processed_dir> <input_data_directory> <dsd_directory>"
    echo "Example: ./run_custom_dataset.sh my_dataset ../my_data_folder/my_dataset ../raw_data/DATA ../raw_data/DSD"
    exit 1
fi

DATASET_NAME="$1"
PROCESSED_DIR="$2"
INPUT_DATA_DIR="$3"
DSD_DIR="$4"
LOG_DIR="logs/${DATASET_NAME}_validation_logs"

echo "======================================================="
echo "Running Validation Suite for: $DATASET_NAME"
echo "Processed Directory: $PROCESSED_DIR"
echo "Input Data: $INPUT_DATA_DIR"
echo "DSD Directory: $DSD_DIR"
echo "Logs will be saved to: un_dataset_validator/$LOG_DIR"
echo "======================================================="

# Ensure we're in the validation directory relative to where the script is run
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Run the python validation suite
python3 scripts/run_validations.py --dataset "$DATASET_NAME" --dataset_dir "$PROCESSED_DIR" --input_data_dir "$INPUT_DATA_DIR" --dsd_dir "$DSD_DIR" --rule all --log_dir "$LOG_DIR"

if [ $? -eq 0 ]; then
    echo "Validation completed successfully!"
else
    echo "Validation finished with errors. Please review the logs."
fi

echo "Summary report generated at: un_dataset_validator/$LOG_DIR/summary.md"
