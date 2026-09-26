#!/bin/bash
set -euo pipefail

# Multi-File CSV Sharder and Processor
# This script orchestrates the sharding of multiple large CSV files
# and then processes the resulting smaller shards in parallel with bounded concurrency and retries.

function split_csv {
    local file="$1"
    local output_dir="$2"
    local lines_per_shard="$3"
    
    if [ ! -f "$file" ]; then
        echo "ERROR: Input file does not exist or is not a regular file: $file" >&2
        return 1
    fi

    local header
    header=$(head -n 1 "$file")
    local fname
    fname=$(basename "$file" | sed 's/\.csv$//')
    
    tail -n +2 "$file" | \
      split -l "$lines_per_shard" - "$output_dir/${fname}_shard_" --additional-suffix=.csv

    shopt -s nullglob
    local generated_shards=("$output_dir/${fname}_shard_"*.csv)
    if [ ${#generated_shards[@]} -eq 0 ]; then
        echo "ERROR: split failed to produce any shards for $file" >&2
        return 1
    fi

    for i in "${generated_shards[@]}"; do
      sed -i -e "1i$header" "$i"
    done
}

# --- Configuration Variables ---
SHARD_DIR="shards"
# Directory where your 45 large input CSV files are located.
INPUT_DIR="gcs_output/input_files"

# Directory where operational counters will be saved.
COUNTERS_DIR="counters"

# Directory where the final processed output files will be saved.
OUTPUT_FINAL_DIR="gcs_output/output"

# Number of parallel workers for processing shards.
PARALLELISM=${PARALLELISM:-8}

# Rows per shard chunk.
SHARD_ROWS=500000

# Name/path of your processing Python script.
STATVAR_PROCESSOR_SCRIPT="../../tools/statvar_importer/stat_var_processor.py"

# --- Setup Directories ---
echo "Creating necessary directories..."
mkdir -p "$OUTPUT_FINAL_DIR"
mkdir -p "$SHARD_DIR"
mkdir -p "$COUNTERS_DIR"
echo "Directories created/ensured: $OUTPUT_FINAL_DIR, $SHARD_DIR, $COUNTERS_DIR"

# --- Step 1: Shard the main input files ---
# This loop iterates through each of your 45 large CSV files
# and uses your `split_csv` function to shard them into 500k row chunks.
echo "--- Step 1: Sharding large input CSV files into 500k row chunks ---" >&2
shopt -s nullglob
source_files=("$INPUT_DIR"/*.csv)
if [ ${#source_files[@]} -eq 0 ]; then
    echo "ERROR: No CSV files found in '$INPUT_DIR' to shard." >&2
    exit 1
fi

sharded_count=0
for source_file in "${source_files[@]}"; do
    [[ "$source_file" == *"shard"* ]] && continue
    echo "Sharding: $source_file" >&2
    split_csv "$source_file" "$SHARD_DIR" "$SHARD_ROWS"
    (( sharded_count++ )) || true
done

if [ "$sharded_count" -eq 0 ]; then
    echo "ERROR: No valid source CSV files were sharded from '$INPUT_DIR'." >&2
    exit 1
fi
echo "--- Step 1: Sharding complete. Sharded $sharded_count source file(s). ---" >&2

# --- Step 2: Process the generated shards in parallel with retries ---
echo "--- Step 2: Processing generated CSV shards (Parallelism: $PARALLELISM) ---" >&2
shards=("$SHARD_DIR"/*_shard_*.csv)
if [ ${#shards[@]} -eq 0 ]; then
    echo "ERROR: No shard files found matching '$SHARD_DIR/*_shard_*.csv'. Sharding failed or produced no output." >&2
    echo "Please ensure your 'split_csv' generates files in the '$SHARD_DIR' and follows the '*_shard_*.csv' naming convention." >&2
    exit 1
fi

process_shard() {
    local file="$1"
    local prefix
    prefix=$(basename "$file" | cut -d'.' -f1)
    
    echo "INFO: Processing shard: $file (Prefix: $prefix)" >&2
    
    local success=0
    for attempt in 1 2 3; do
        rm -f "$OUTPUT_FINAL_DIR/output_${prefix}"* "$COUNTERS_DIR/counters_${prefix}.csv"
        if python3 "$STATVAR_PROCESSOR_SCRIPT" \
            --input_data="$file" \
            --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
            --pv_map="censuscountybusinesspatterns_pvmap.csv" \
            --config_file="censuscountybusinesspatterns_metadata.csv" \
            --output_path="$OUTPUT_FINAL_DIR/output_${prefix}" \
            --counters_print_interval=-1 \
            --output_counters="$COUNTERS_DIR/counters_${prefix}.csv" && \
            [ -s "$OUTPUT_FINAL_DIR/output_${prefix}.csv" ] && \
            [ "$(wc -l < "$OUTPUT_FINAL_DIR/output_${prefix}.csv")" -gt 1 ]; then
            success=1
            break
        fi
        echo "WARNING: Processor failed on shard $file (Attempt $attempt/3). Retrying in 15s..." >&2
        sleep 15
    done

    if [ "$success" -ne 1 ]; then
        rm -f "$OUTPUT_FINAL_DIR/output_${prefix}"* "$COUNTERS_DIR/counters_${prefix}.csv"
        echo "ERROR: Processor failed on shard $file after 3 attempts. Aborting." >&2
        return 1
    fi
    return 0
}

active_jobs=0
job_failed=0

for file in "${shards[@]}"; do
    if [ "$job_failed" -ne 0 ]; then
        break
    fi

    process_shard "$file" &
    (( active_jobs++ )) || true

    if [ "$active_jobs" -ge "$PARALLELISM" ]; then
        if ! wait -n; then
            echo "ERROR: A shard processing job failed." >&2
            job_failed=1
        fi
        (( active_jobs-- )) || true
    fi
done

# Wait for remaining background jobs to finish
while [ "$active_jobs" -gt 0 ]; do
    if ! wait -n; then
        echo "ERROR: A shard processing job failed." >&2
        job_failed=1
    fi
    (( active_jobs-- )) || true
done

if [ "$job_failed" -ne 0 ]; then
    echo "ERROR: Shard processing encountered failures. Pipeline aborted." >&2
    exit 1
fi

echo "--- Step 2: All shard processing complete. ---" >&2

# --- Final Cleanup / Summary ---
echo "--- Workflow Complete ---"
echo "All input files have been sharded and processed."
echo "Final processed outputs are in: $OUTPUT_FINAL_DIR"
echo "Operational counters are in: $COUNTERS_DIR"
