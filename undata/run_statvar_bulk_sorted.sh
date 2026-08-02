#!/bin/bash

# Configuration
BASE_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/undata"
DETERMINISTIC_DIR="${BASE_DIR}/SDG/output/deterministic"
TOOLS_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/tools"
VENV_PATH="/usr/local/google/home/nehil/datacommons/import/git/data/venv"
ROW_COUNTS_CSV="/usr/local/google/home/nehil/datacommons/import/git/data/sdg_file_row_counts.csv"
LOG_DIR="${BASE_DIR}/logs"
RUN_LOG="${LOG_DIR}/bulk_run.log"
OUTPUT_COUNTS_CSV="${LOG_DIR}/output_row_counts.csv"
PLACES_RESOLVED_CSV="${BASE_DIR}/DESA/all_places.csv"

# Limit parameter
LIMIT=$1
count=0

# Ensure directories exist
mkdir -p "${LOG_DIR}"

# Initialize log files
echo "=== Bulk Run Started: $(date) ===" > "${RUN_LOG}"
echo "dataset_name,output_row_count" > "${OUTPUT_COUNTS_CSV}"

# Activate virtual environment
source "${VENV_PATH}/bin/activate"

# Read CSV, skip header, sort numeric by 2nd col (ascending), loop
tail -n +2 "${ROW_COUNTS_CSV}" | sort -t ',' -k2,2n | while IFS=',' read -r filename row_count; do
    # Strip extension
    DATASET_NAME="${filename%.csv}"
    DATASET_DIR="${DETERMINISTIC_DIR}/${DATASET_NAME}"

    # Check if directory exists
    if [ ! -d "${DATASET_DIR}" ]; then
        continue
    fi

    # Check limit
    if [[ -n "${LIMIT}" && "${count}" -ge "${LIMIT}" ]]; then
        echo "Limit of ${LIMIT} reached. Stopping." | tee -a "${RUN_LOG}"
        break
    fi

    echo "Processing dataset: ${DATASET_NAME} (Rows: ${row_count})..." | tee -a "${RUN_LOG}"
    
    mkdir -p "${DATASET_DIR}/validation"

    # Run statvar processor
    python3 "${TOOLS_DIR}/statvar_importer/stat_var_processor.py" \
      --input_data="${DATASET_DIR}/input/data.csv" \
      --config_file="${DATASET_DIR}/deterministic_metadata.csv" \
      --pv_map="${DATASET_DIR}/deterministic_pvmap.csv" \
      --places_resolved_csv="${PLACES_RESOLVED_CSV}" \
      --output_path="${DATASET_DIR}/output" \
      --output_counters="${DATASET_DIR}/validation/statvar_processor_counters.csv" >> "${RUN_LOG}" 2>&1

    # Record output row counts
    OUTPUT_FILE="${DATASET_DIR}/output.csv"
    if [ -f "${OUTPUT_FILE}" ]; then
        # Count rows minus header
        OUT_COUNT=$(wc -l < "${OUTPUT_FILE}")
        OUT_COUNT=$((OUT_COUNT - 1))
        echo "${DATASET_NAME},${OUT_COUNT}" >> "${OUTPUT_COUNTS_CSV}"
    else
        echo "${DATASET_NAME},FAILED" >> "${OUTPUT_COUNTS_CSV}"
    fi

    count=$((count + 1))
done

echo "=== Bulk Run Completed: $(date) ===" | tee -a "${RUN_LOG}"
deactivate
