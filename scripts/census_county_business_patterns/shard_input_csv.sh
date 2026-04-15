#!/bin/bash

# Multi-File CSV Sharder and Processor
# This script orchestrates the sharding of multiple large CSV files
# and then processes the resulting smaller shards in parallel.

# --- Helper Functions for Job Management ---

# Function to count running background jobs by name or total
function num_jobs {
    local name="$1"
    if [[ -z "$name" ]]; then
        # Count all background jobs for this shell
        echo $(jobs -r | wc -l) >&2
    else
        # Count processes whose command line contains the given name
        # Exclude grep processes themselves
        echo $(pgrep -f "$name" | wc -l) >&2
    fi
}

# Function to pause script execution until active jobs are below a limit
function sleep_while_active {
    local max_jobs=$1
    local job_name="$2" # Optional: specific process name to monitor
    local current_jobs=$(num_jobs "$job_name")

    echo "INFO: Currently active jobs for '$job_name': $current_jobs (Max: $max_jobs)" >&2
    while (( current_jobs >= max_jobs )); do
        echo "INFO: Max jobs ($max_jobs) reached. Waiting for a job to complete..." >&2
        sleep 500 # Wait for 5 seconds before re-checking
        current_jobs=$(num_jobs "$job_name")
        echo "INFO: Re-checking active jobs for '$job_name': $current_jobs" >&2
    done
}
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
# Set the maximum number of parallel processes to run.
# Adjust based on your system's CPU cores and memory.
PARALLELISM=3
SHARD_DIR="shards"
# Directory where your 45 large input CSV files are located.
INPUT_DIR="gcs_output/input_files"

# Directory where intermediate debug outputs (like counters) will be saved.
DEBUG_DIR="./debug_outputs"

# Directory where the final processed output files will be saved.
OUTPUT_FINAL_DIR="gcs_output/output"

# Path to your existing CSV splitting script.
# Make sure this script exists and is executable (chmod +x).
# SPLIT_CSV_SCRIPT="../../tools/split_csv.sh"

# Name/path of your processing Python script.
STATVAR_PROCESSOR_SCRIPT="../../tools/statvar_importer/stat_var_processor.py"

# --- Setup Directories ---
echo "Creating necessary directories..."
mkdir -p "$DEBUG_DIR"
mkdir -p "$OUTPUT_FINAL_DIR"
mkdir -p "$SHARD_DIR"
echo "Directories created/ensured: $DEBUG_DIR, $OUTPUT_FINAL_DIR"
SHARD_ROWS=500000
# --- Step 1: Shard the main input files ---
# This loop iterates through each of your 45 large CSV files
# and uses your `split_csv.sh` script to shard them into 100k row chunks.
# The shards will typically be created in the same directory as the source_file
# or a location handled by split_csv.sh. Ensure split_csv.sh handles the output naming correctly.
echo "--- Step 1: Sharding large input CSV files into 100k row chunks ---"
# Loop over all .csv files in the INPUT_DIR, excluding any files already named as shards
for source_file in "$INPUT_DIR"/*.csv; do
    [[ "$source_file" == *"shard"* ]] && continue
    echo "Sharding: $source_file" >&2
    # Execute the split_csv.sh script for each large input file
    # This script is assumed to handle the creation of *_shard_*.csv files.
    split_csv "$source_file" $SHARD_DIR $SHARD_ROWS
    # You might want to add sleep_while_active here if split_csv.sh itself is CPU intensive
    # and you want to limit how many split_csv.sh instances run in parallel.
done
echo "--- Step 1: Sharding complete. ---" >&2

# --- Step 2: Process the generated shards in parallel ---
# This loop iterates over all the newly created shard files and processes them
# using your `statvar_processpr.py` script.
echo "--- Step 2: Processing generated CSV shards in parallel ---" >&2
# Loop over all files that match the shard pattern
# Assuming shards are created in INPUT_DIR with a '_shard_' pattern.
# Adjust the glob pattern `*` if your shard names are more specific.
for file in "$SHARD_DIR"/*_shard_*.csv; do
    if [ -f "$file" ]; then # Ensure it's a regular file
        # Extract the base name (e.g., "my_data_file_shard_1")
        prefix=$(basename "$file" | cut -d'.' -f1)
        
        echo "INFO: Processing shard: $file (Prefix: $prefix)" >&2
        
        # Execute the Python processing script in the background (&)
        # We assume statvar_processpr.py takes these arguments.
        # If there are other arguments (the '...' in your original snippet), add them here.
        python3 "$STATVAR_PROCESSOR_SCRIPT" \
            --input_data="$file" \
            --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
            --pv_map="censuscountybusinesspatterns_pvmap.csv" \
            --config_file="censuscountybusinesspatterns_metadata.csv" \
            --output_path="$OUTPUT_FINAL_DIR/output_${prefix}" \
            --counters_print_interval=-1
            # --output_counters="$DEBUG_DIR/counters_${prefix}" \ # uncomment this line to debug the script like to get the details like memory utlization etc.
            # Add any other required arguments for statvar_processpr.py here \
            # Run in background
        
        # Manage parallelism: pause if too many jobs are running
        # We monitor the 'statvar_processpr.py' script's processes.
        # sleep_while_active "$PARALLELISM" "$STATVAR_PROCESSOR_SCRIPT"
    else
        echo "WARNING: No shard files found matching '$INPUT_DIR/*_shard_*.csv' or '$file' is not a regular file."
        echo "Please ensure your 'split_csv.sh' generates files in the '$INPUT_DIR' and follows the '*_shard_*.csv' naming convention."
    fi
done

# Wait for all background jobs to complete before exiting the script.
echo "--- Step 2: All processing jobs submitted. Waiting for them to finish... ---"
wait
echo "--- Step 2: All parallel processing complete. ---"

# --- Final Cleanup / Summary (Optional) ---
echo "--- Workflow Complete ---"
echo "All input files have been sharded and processed."
echo "Final processed outputs are in: $OUTPUT_FINAL_DIR"
echo "Debug counters are in: $DEBUG_DIR"