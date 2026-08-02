#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

DATA_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/data"
METADATA_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/metadata_unreviewed"
OUTPUT_BASE_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/unreviewed"
LOG_DIR="undata/logs"
GCS_OUTPUT_DIR="gs://undata/desa-gender/2025/transcoded/output/unreviewed"
GEMINI_PATH="/google/bin/images/image-6a01372e-0000-20fd-aeb3-883d24fe0d58/gemini --noproxy"
DC_IMPORT_JAR=${DC_IMPORT_JAR:-"/tmp/datacommons-import-tool.jar"}
MAX_PARALLEL=3
RETRY_FILE="undata/logs/retry_list.txt"

mkdir -p "$OUTPUT_BASE_DIR"
mkdir -p "$LOG_DIR"
touch "$RETRY_FILE"

# Function to check if processing was successful
is_successful() {
    local dataset_dir="$1"
    local filename="$2"
    
    # Check if all critical files exist and are non-empty
    if [ ! -s "$dataset_dir/output.csv" ] || \
       [ ! -s "$dataset_dir/output.tmcf" ] || \
       [ ! -s "$dataset_dir/output_stat_vars.mcf" ]; then
        return 1
    fi
    
    # Check if output.csv has at least 2 lines (header + data)
    local line_count=$(wc -l < "$dataset_dir/output.csv")
    if [ "$line_count" -lt 2 ]; then
        return 1
    fi
    
    return 0
}

# Function to run validation
run_validate_output() {
    local filename="$1"
    local output_folder="$2"
    local dataset_log="$3"

    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Starting Validation (dc-import)..." >> "$dataset_log" 2>&1
    mkdir -p "$output_folder/validation"
    
    if [ ! -f "$DC_IMPORT_JAR" ]; then
        echo "Warning: DC_IMPORT_JAR not found at $DC_IMPORT_JAR. Attempting to find it..." >> "$dataset_log" 2>&1
        local found_jar=$(find . -name "datacommons-import-tool*.jar" | head -n 1)
        if [ -n "$found_jar" ]; then
            DC_IMPORT_JAR="$found_jar"
            echo "Found JAR at $DC_IMPORT_JAR" >> "$dataset_log" 2>&1
        else
            echo "Error: DC_IMPORT_JAR not found. Skipping validation." >> "$dataset_log" 2>&1
            return 1
        fi
    fi

    # Run dc-import tool
    java -jar "$DC_IMPORT_JAR" genmcf -n 20 -r FULL \
      "$output_folder"/output*.{csv,tmcf,mcf} \
      -o "$output_folder/validation" >> "$dataset_log" 2>&1

    # Run import validator
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Running import validator..." >> "$dataset_log" 2>&1
    ./venv/bin/python3 tools/import_validation/runner.py \
        --validation_config=tools/import_validation/validation_config.json \
        --stats_summary="$output_folder/validation/summary_report.csv" \
        --lint_report="$output_folder/validation/report.json" \
        --validation_output="$output_folder/validation/validation-result.json" >> "$dataset_log" 2>&1
    
    return $?
}

# Function to run stat_var_processor
run_stat_var_processor() {
    local filename="$1"
    local f="$2"
    local output_folder="$3"
    local metadata_file="$4"
    local dataset_log="$5"

    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Starting StatVar Processor..." >> "$dataset_log" 2>&1
    local counters_file="$output_folder/validation/statvar_processor_counters.csv"
    mkdir -p "$output_folder/validation"
    local output_path="$output_folder/output"
    
    # pvmap_generator outputs to $output_folder/output_pvmap.csv
    local pvmap_file="$output_folder/output_pvmap.csv"
    
    ./venv/bin/python3 tools/statvar_importer/stat_var_processor.py \
      --input_data="$f" \
      --config_file="$metadata_file" \
      --pv_map="$pvmap_file" \
      --output_path="$output_path" \
      --output_counters="$counters_file" >> "$dataset_log" 2>&1

    if [ ! -f "$counters_file" ]; then
        echo "Error: Unable to find output counters: $counters_file" >> "$dataset_log" 2>&1
        return 1
    fi
    
    local statvar_errors=$(grep error "$counters_file")
    if [ -n "$statvar_errors" ]; then
        local num_errors=$(wc -l <<< "$statvar_errors")
        echo "Statvar Processor had ${num_errors} errors: $statvar_errors" >> "$dataset_log" 2>&1
    fi
    
    local num_inputs=$(grep "input-numeric-values" "$counters_file" | cut -d, -f2 | tr -d '\r')
    num_inputs=${num_inputs:-"1"}
    local num_outputs=$(grep "output-svobs-csv-rows" "$counters_file" | cut -d, -f2 | tr -d '\r')
    num_outputs=${num_outputs:-"0"}
    
    local percent_processed=$(bc <<< "100 * $num_outputs / $num_inputs")
    local min_percent=10
    
    if (( percent_processed < min_percent )); then
        echo "Error: Only $percent_processed percent inputs in $f processed ($num_outputs/$num_inputs). Check output/configs." >> "$dataset_log" 2>&1
        return 1
    fi
    
    echo "Successfully completed statvar processor for $filename ($percent_processed% processed)." >> "$dataset_log" 2>&1
    return 0
}

# Function to process a single dataset
process_dataset() {
    local f="$1"
    local is_retry="${2:-false}"
    local filename=$(basename "$f" .csv)
    local metadata_file="$METADATA_DIR/${filename}_metadata.csv"
    local output_folder="$OUTPUT_BASE_DIR/$filename"
    local dataset_log="$LOG_DIR/${filename}.log"

    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting $filename (is_retry=$is_retry)"
    
    if [ ! -f "$metadata_file" ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Warning: Metadata for $filename not found. Skipping."
        return
    fi

    if is_successful "$output_folder" "$filename"; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Info: $filename already successful. Syncing..."
        
        # Calculate efficacy for this specific dataset
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Calculating efficacy..." >> "$dataset_log" 2>&1
        local efficacy_output=$(./venv/bin/python3 undata/DESA/calculate_efficacy.py "$filename")
        echo "$efficacy_output" >> "$dataset_log" 2>&1
        
        # Upload HTML to GCS
        gcloud storage cp "undata/DESA/efficacy_results/${filename}_Agent_Efficacy_Board.html" "gs://undata/desa-gender/2025/transcoded/efficacy_results/" >> "$dataset_log" 2>&1
        
        gcloud storage cp -r "$output_folder" "$GCS_OUTPUT_DIR/" >> "$dataset_log" 2>&1
        return
    fi

    mkdir -p "$output_folder"
    
    # Stage 1: PV Map Generation
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Stage 1: pvmap_generator" >> "$dataset_log"

    # Random sleep to jitter requests and avoid 429s
    sleep_time=$(( RANDOM % 30 + 10 ))
    echo "Sleeping for $sleep_time seconds before Gemini call..." >> "$dataset_log"
    sleep "$sleep_time"

    ./venv/bin/python3 tools/agentic_import/pvmap_generator.py \
      --input_data="$f" \
      --input_metadata="undata/metadata.csv,$metadata_file" \
      --output_path="$output_folder/output" \
      --skip_confirmation \
      --gemini_cli="$GEMINI_PATH" >> "$dataset_log" 2>&1
    
    local status=$?
    if [ $status -ne 0 ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] FAILED at Stage 1 (PV Map)" | tee -a "$dataset_log"
        echo "$f" >> "$RETRY_FILE"
        return 1
    fi

    # Stage 2: StatVar Processor
    if ! run_stat_var_processor "$filename" "$f" "$output_folder" "$metadata_file" "$dataset_log"; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] FAILED at Stage 2 (StatVar)" | tee -a "$dataset_log"
        echo "$f" >> "$RETRY_FILE"
        return 1
    fi

    # Stage 3: Validation (SKIPPED for now)
    # if ! run_validate_output "$filename" "$output_folder" "$dataset_log"; then
    #     echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] FAILED at Stage 3 (Validation)" | tee -a "$dataset_log"
    #     echo "$f" >> "$RETRY_FILE"
    #     return 1
    # fi

    if is_successful "$output_folder" "$filename"; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Successfully processed. Calculating efficacy..." | tee -a "$dataset_log"
        
        # Calculate efficacy for this specific dataset
        local efficacy_output=$(./venv/bin/python3 undata/DESA/calculate_efficacy.py "$filename")
        echo "$efficacy_output" >> "$dataset_log" 2>&1
        
        # Upload HTML to GCS
        gcloud storage cp "undata/DESA/efficacy_results/${filename}_Agent_Efficacy_Board.html" "gs://undata/desa-gender/2025/transcoded/efficacy_results/" >> "$dataset_log" 2>&1
        
        gcloud storage cp -r "$output_folder" "$GCS_OUTPUT_DIR/" >> "$dataset_log" 2>&1
    else
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$filename] Final check failed" | tee -a "$dataset_log"
        echo "$f" >> "$RETRY_FILE"
        return 1
    fi
}

# Export functions for parallel execution
export -f process_dataset
export -f is_successful
export -f run_stat_var_processor
export -f run_validate_output
export DATA_DIR METADATA_DIR OUTPUT_BASE_DIR LOG_DIR GCS_OUTPUT_DIR GEMINI_PATH DC_IMPORT_JAR RETRY_FILE

# Run processing in parallel using xargs if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    mkdir -p "$OUTPUT_BASE_DIR"
    mkdir -p "$LOG_DIR"
    touch "$RETRY_FILE"

    # Using a temporary file to list all csv files to avoid command line length issues
    find "$DATA_DIR" -name "*.csv" | xargs -I {} -P "$MAX_PARALLEL" bash -c "source undata/run_batch_import.sh; process_dataset '{}'"

    echo "Batch import process initiated/resumed for all files."
fi
