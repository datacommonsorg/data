#!/bin/bash

# Configuration
# Run this script from /usr/local/google/home/nehil/datacommons/import/git/data/undata
BASE_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/undata"
AGENTIC_DIR="${BASE_DIR}/SDG/output/agentic"
TOOLS_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/tools"
VENV_PATH="/usr/local/google/home/nehil/datacommons/import/git/data/venv"
GEMINI_BIN="/google/bin/releases/gemini-cli/tools/gemini --noproxy -y"

PLACES_RESOLVED_CSV="${BASE_DIR}/DESA/all_places.csv"

# Optional: Process a specific dataset provided as an argument
SINGLE_DATASET=$1

echo "=== Pipeline Start ==="
source "${VENV_PATH}/bin/activate"

# Capture original keys
export ORIG_GOOGLE_API_KEY=$GOOGLE_API_KEY
export ORIG_GEMINI_API_KEY=$GEMINI_API_KEY

# Set Gemini API key for tools
export GEMINI_API_KEY="${ORIG_GEMINI_API_KEY}"
unset GOOGLE_API_KEY

process_dataset() {
  local DATASET_DIR="$1"
  if [ ! -d "${DATASET_DIR}" ]; then
    echo "Directory not found: ${DATASET_DIR}"
    return
  fi

  local DATASET_NAME=$(basename "${DATASET_DIR}")
  
  echo "=========================================================="
  echo "Processing Dataset: ${DATASET_NAME}"
  
  local INPUT_DATA="${DATASET_DIR}/input/data.csv"
  local INPUT_METADATA="${DATASET_DIR}/input/metadata.csv"
  local EXISTING_METADATA="${DATASET_DIR}/deterministic_metadata.csv"
  local EXISTING_PVMAP="${DATASET_DIR}/deterministic_pvmap.csv"
  
  if [[ ! -f "${INPUT_DATA}" || ! -f "${INPUT_METADATA}" ]]; then
    echo "Skipping ${DATASET_NAME}: Missing input files."
    return
  fi

  # Clean up previous generated files to ensure we are rerunning
  rm -rf "${DATASET_DIR}/generated"
  mkdir -p "${DATASET_DIR}/generated"

  echo "=== 1. Running PV Map Generator (Gemini) ==="
  
  # Ensure environment is clean for this sub-process
  GOOGLE_API_KEY="" 
  python3 "${TOOLS_DIR}/agentic_import/pvmap_generator.py" \
    --gemini_cli="${GEMINI_BIN}" \
    --input_data="${INPUT_DATA}" \
    --input_metadata="${INPUT_METADATA}" \
    --extra_instruction_files="${EXISTING_PVMAP}" \
    --places_resolved_csv="${PLACES_RESOLVED_CSV}" \
    --output_path="${DATASET_DIR}/generated/new" \
    --skip_confirmation=True
  
  echo "=== 2. Running StatVar Processor ==="
  mkdir -p "${DATASET_DIR}/validation"
  mkdir -p "${DATASET_DIR}/output"

  # Use the newly generated pvmap if available
  local PVMAP_TO_USE="${DATASET_DIR}/generated/new_pvmap.csv"
  if [ ! -f "${PVMAP_TO_USE}" ]; then
    echo "Warning: ${PVMAP_TO_USE} not found. Gemini likely failed. Skipping processor."
    return
  fi

  python3 "${TOOLS_DIR}/statvar_importer/stat_var_processor.py" \
    --input_data="${INPUT_DATA}" \
    --config_file="${EXISTING_METADATA}" \
    --pv_map="${PVMAP_TO_USE}" \
    --places_resolved_csv="${PLACES_RESOLVED_CSV}" \
    --output_path="${DATASET_DIR}/output/output" \
    --output_counters="${DATASET_DIR}/validation/statvar_processor_counters.csv"

  echo "Finished processing ${DATASET_NAME}"
  sleep 2
}

if [ -n "${SINGLE_DATASET}" ]; then
  # If argument is a full path, use it. If it's just a name, append to AGENTIC_DIR.
  if [[ "${SINGLE_DATASET}" == /* ]]; then
    process_dataset "${SINGLE_DATASET}"
  else
    process_dataset "${AGENTIC_DIR}/${SINGLE_DATASET}"
  fi
else
  ORDER_FILE="/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/zero_count_datasets.txt"
  echo "=== Rerunning for datasets with 0 rows from ${ORDER_FILE} ==="
  if [[ ! -f "${ORDER_FILE}" ]]; then
    echo "Order file not found: ${ORDER_FILE}"
    exit 1
  fi
  
  while read -r dir_name; do
    if [[ -z "${dir_name}" ]]; then continue; fi
    DATASET_PATH="${AGENTIC_DIR}/${dir_name}"
    
    if [ -d "${DATASET_PATH}" ]; then
      process_dataset "${DATASET_PATH}"
    else
      echo "Directory not found in agentic folder: ${DATASET_PATH}"
    fi
  done < "${ORDER_FILE}"
fi

echo "=== Pipeline Complete ==="
export GOOGLE_API_KEY=$ORIG_GOOGLE_API_KEY
deactivate
