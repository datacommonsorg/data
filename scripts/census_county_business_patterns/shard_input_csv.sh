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
    
    # Stream-inject the CSV header directly into each shard during split, eliminating sed -i rewrites
    tail -n +2 "$file" | \
      split -l "$lines_per_shard" \
            --filter="head -n 1 \"$file\" > \"\$FILE\"; cat >> \"\$FILE\"" \
            - "$output_dir/${fname}_shard_" --additional-suffix=.csv

    shopt -s nullglob
    local generated_shards=("$output_dir/${fname}_shard_"*.csv)
    if [ ${#generated_shards[@]} -eq 0 ]; then
        echo "ERROR: split failed to produce any shards for $file" >&2
        return 1
    fi
}

# --- Configuration Variables ---
SHARD_DIR="shards"
# Directory where your 45 large input CSV files are located.
INPUT_DIR="gcs_output/input_files"


# Directory where the final processed output files will be saved.
OUTPUT_FINAL_DIR="gcs_output/output"

# Concurrency configuration:
# Dynamically scale workers up to 48 based on available CPU cores.
# On a 64-core Cloud Batch VM (n2-highmem-64 with 512GB RAM), this scales to 48 parallel workers,
# allowing ~55 shards to be processed in almost a single wave while leaving cores for I/O.
NUM_CPUS=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 8)
if [ "$NUM_CPUS" -ge 64 ]; then
    AUTO_PARALLELISM=48
elif [ "$NUM_CPUS" -ge 16 ]; then
    AUTO_PARALLELISM=$(( NUM_CPUS * 3 / 4 ))
elif [ "$NUM_CPUS" -ge 4 ]; then
    AUTO_PARALLELISM=$(( NUM_CPUS ))
else
    AUTO_PARALLELISM=2
fi
PARALLELISM=${PARALLELISM:-$AUTO_PARALLELISM}

# Rows per shard chunk (tuned to 1,000,000 to halve total shards and reduce schema parsing overhead).
SHARD_ROWS=${SHARD_ROWS:-1000000}

# Name/path of your processing Python script.
STATVAR_PROCESSOR_SCRIPT="../../tools/statvar_importer/stat_var_processor.py"

# --- Setup Directories & Clean Prior Artifacts ---
echo "Setting up and cleaning working directories..."
mkdir -p "$OUTPUT_FINAL_DIR"
mkdir -p "$SHARD_DIR"
rm -f "$SHARD_DIR"/*_shard_*.csv "$OUTPUT_FINAL_DIR"/output_*
echo "Directories cleaned/ensured: $OUTPUT_FINAL_DIR, $SHARD_DIR"

# --- Step 1: Shard the main input files ---
# This loop iterates through each of your large CSV files in parallel
# and uses your `split_csv` function to shard them into ${SHARD_ROWS} row chunks.
echo "--- Step 1: Sharding large input CSV files into ${SHARD_ROWS} row chunks (Parallelism: $PARALLELISM) ---" >&2
shopt -s nullglob
source_files=("$INPUT_DIR"/*.csv)
if [ ${#source_files[@]} -eq 0 ]; then
    echo "ERROR: No CSV files found in '$INPUT_DIR' to shard." >&2
    exit 1
fi

active_sharding_jobs=0
sharding_failed=0
sharded_count=0

for source_file in "${source_files[@]}"; do
    [[ "$source_file" == *"shard"* ]] && continue
    if [ "$sharding_failed" -ne 0 ]; then
        break
    fi

    echo "Sharding: $source_file" >&2
    split_csv "$source_file" "$SHARD_DIR" "$SHARD_ROWS" &
    (( active_sharding_jobs++ )) || true
    (( sharded_count++ )) || true

    if [ "$active_sharding_jobs" -ge "$PARALLELISM" ]; then
        if ! wait -n; then
            echo "ERROR: A sharding job failed." >&2
            sharding_failed=1
            kill $(jobs -p) 2>/dev/null || true
            break
        fi
        (( active_sharding_jobs-- )) || true
    fi
done

# Wait for remaining background sharding jobs to finish
if [ "$sharding_failed" -eq 0 ]; then
    while [ "$active_sharding_jobs" -gt 0 ]; do
        if ! wait -n; then
            echo "ERROR: A sharding job failed." >&2
            sharding_failed=1
            kill $(jobs -p) 2>/dev/null || true
            break
        fi
        (( active_sharding_jobs-- )) || true
    done
fi

if [ "$sharding_failed" -ne 0 ]; then
    echo "ERROR: Sharding encountered failures. Pipeline aborted." >&2
    exit 1
fi

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

# Download schema MCF once locally before spawning workers to eliminate redundant 90 MB GCS downloads across shards
SCHEMA_GCS_URI="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
LOCAL_STATVAR_MCF="$SHARD_DIR/stat_vars.mcf"

echo "Downloading schema MCF from $SCHEMA_GCS_URI once for all workers..." >&2
if ! python3 -c "import sys; sys.path.insert(0, '../../util'); from file_util import file_copy; file_copy('$SCHEMA_GCS_URI', '$LOCAL_STATVAR_MCF')"; then
    echo "ERROR: Failed to download $SCHEMA_GCS_URI to $LOCAL_STATVAR_MCF" >&2
    exit 1
fi

process_shard() {
    local file="$1"
    local prefix
    prefix=$(basename "$file" | cut -d'.' -f1)
    
    echo "INFO: Processing shard: $file (Prefix: $prefix)" >&2
    
    local success=0
    for attempt in 1 2 3; do
        rm -f "$OUTPUT_FINAL_DIR/output_${prefix}"*
        if python3 "$STATVAR_PROCESSOR_SCRIPT" \
            --input_data="$file" \
            --existing_statvar_mcf="$LOCAL_STATVAR_MCF" \
            --pv_map="censuscountybusinesspatterns_pvmap.csv" \
            --config_file="censuscountybusinesspatterns_metadata.csv" \
            --output_path="$OUTPUT_FINAL_DIR/output_${prefix}" \
            --counters_print_interval=-1 && \
            [ -s "$OUTPUT_FINAL_DIR/output_${prefix}.csv" ] && \
            [ "$(wc -l < "$OUTPUT_FINAL_DIR/output_${prefix}.csv")" -gt 1 ]; then
            success=1
            break
        fi
        if [ "$attempt" -lt 3 ]; then
            echo "WARNING: Processor failed on shard $file (Attempt $attempt/3). Retrying in 15s..." >&2
            sleep 15
        else
            echo "WARNING: Processor failed on shard $file (Attempt $attempt/3)." >&2
        fi
    done

    if [ "$success" -ne 1 ]; then
        rm -f "$OUTPUT_FINAL_DIR/output_${prefix}"*
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
            kill $(jobs -p) 2>/dev/null || true
            break
        fi
        (( active_jobs-- )) || true
    fi
done

# Wait for remaining background jobs to finish if no failure occurred
if [ "$job_failed" -eq 0 ]; then
    while [ "$active_jobs" -gt 0 ]; do
        if ! wait -n; then
            echo "ERROR: A shard processing job failed." >&2
            job_failed=1
            kill $(jobs -p) 2>/dev/null || true
            break
        fi
        (( active_jobs-- )) || true
    done
fi

# Clean up temporary local schema MCF
rm -f "$LOCAL_STATVAR_MCF"

if [ "$job_failed" -ne 0 ]; then
    echo "ERROR: Shard processing encountered failures. Pipeline aborted." >&2
    exit 1
fi

echo "--- Step 2: All shard processing complete. ---" >&2

# --- Final Cleanup / Summary ---
echo "--- Workflow Complete ---"
echo "All input files have been sharded and processed."
echo "Final processed outputs are in: $OUTPUT_FINAL_DIR"
