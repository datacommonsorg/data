#!/bin/bash

# Multi-File CSV Sharder and Processor
# This script orchestrates the sharding of multiple large CSV files
# and then processes the resulting smaller shards sequentially with retries.

function split_csv {
    local file=$1; shift
    local output_dir=$1; shift
    local lines_per_shard=$1; shift
    
    local header=$(head -1 $file)
    local fname=$(basename $file | sed 's/\.csv$//')
    tail -n +2 $file | \
      split -l $lines_per_shard - $output_dir/${fname}_shard_ --additional-suffix=.csv
    for i in $output_dir/${fname}_shard_*; do
      sed -i -e "1i$header" "$i"
    done
}

# --- Configuration Variables ---
SHARD_DIR="shards"
# Directory where your 45 large input CSV files are located.
INPUT_DIR="gcs_output/input_files"

# Directory where the final processed output files will be saved.
OUTPUT_FINAL_DIR="gcs_output/output"

# Name/path of your processing Python script.
STATVAR_PROCESSOR_SCRIPT="../../tools/statvar_importer/stat_var_processor.py"

# --- Setup Directories ---
echo "Creating necessary directories..."
mkdir -p "$OUTPUT_FINAL_DIR"
mkdir -p "$SHARD_DIR"
echo "Directories created/ensured: $OUTPUT_FINAL_DIR, $SHARD_DIR"
SHARD_ROWS=500000

# --- Step 1: Shard the main input files ---
# This loop iterates through each of your 45 large CSV files
# and uses your `split_csv` function to shard them into 500k row chunks.
echo "--- Step 1: Sharding large input CSV files into 500k row chunks ---"
# Loop over all .csv files in the INPUT_DIR, excluding any files already named as shards
for source_file in "$INPUT_DIR"/*.csv; do
    [[ "$source_file" == *"shard"* ]] && continue
    echo "Sharding: $source_file" >&2
    split_csv "$source_file" $SHARD_DIR $SHARD_ROWS
done
echo "--- Step 1: Sharding complete. ---" >&2

# --- Step 2: Process the generated shards sequentially ---
# This loop iterates over all the newly created shard files and processes them
# sequentially with retries using the stat_var_processor.py script.
echo "--- Step 2: Processing generated CSV shards ---" >&2
# Loop over all files that match the shard pattern
for file in "$SHARD_DIR"/*_shard_*.csv; do
    if [ -f "$file" ]; then # Ensure it's a regular file
        # Extract the base name (e.g., "my_data_file_shard_1")
        prefix=$(basename "$file" | cut -d'.' -f1)
        
        echo "INFO: Processing shard: $file (Prefix: $prefix)" >&2
        
        # Execute the Python processing script with retry on failure
        success=0
        for attempt in 1 2 3; do
            rm -f "$OUTPUT_FINAL_DIR/output_${prefix}"*
            if python3 "$STATVAR_PROCESSOR_SCRIPT" \
                --input_data="$file" \
                --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
                --pv_map="censuscountybusinesspatterns_pvmap.csv" \
                --config_file="censuscountybusinesspatterns_metadata.csv" \
                --output_path="$OUTPUT_FINAL_DIR/output_${prefix}" \
                --counters_print_interval=-1 && [ -s "$OUTPUT_FINAL_DIR/output_${prefix}.csv" ]; then
                success=1
                break
            fi
            echo "WARNING: Processor failed on shard $file (Attempt $attempt/3). Retrying in 15s..." >&2
            sleep 15
        done
        if [ $success -ne 1 ]; then
            rm -f "$OUTPUT_FINAL_DIR/output_${prefix}"*
            echo "ERROR: Processor failed on shard $file after 3 attempts. Aborting." >&2
            exit 1
        fi
    else
        echo "WARNING: No shard files found matching '$INPUT_DIR/*_shard_*.csv' or '$file' is not a regular file."
        echo "Please ensure your 'split_csv' generates files in the '$INPUT_DIR' and follows the '*_shard_*.csv' naming convention."
    fi
done

echo "--- Step 2: All shard processing complete. ---"

# --- Final Cleanup / Summary (Optional) ---
echo "--- Workflow Complete ---"
echo "All input files have been sharded and processed."
echo "Final processed outputs are in: $OUTPUT_FINAL_DIR"
