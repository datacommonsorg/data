#!/bin/bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Script to run statvar processor with clean logging separation
# This script is called from the Gemini prompt template

# Note: Removed set -e to allow backup to run even if processor fails

# Parse command line arguments
PYTHON_INTERPRETER=""
SCRIPT_DIR=""
WORKING_DIR=""
INPUT_DATA=""
GEMINI_RUN_ID=""
OUTPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --python)
      PYTHON_INTERPRETER="$2"
      shift 2
      ;;
    --script-dir)
      SCRIPT_DIR="$2"
      shift 2
      ;;
    --working-dir)
      WORKING_DIR="$2"
      shift 2
      ;;
    --input-data)
      INPUT_DATA="$2"
      shift 2
      ;;
    --gemini-run-id)
      GEMINI_RUN_ID="$2"
      shift 2
      ;;
    --output-path)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [[ -z "$PYTHON_INTERPRETER" || -z "$SCRIPT_DIR" || -z "$WORKING_DIR" || -z "$INPUT_DATA" || -z "$GEMINI_RUN_ID" || -z "$OUTPUT_PATH" ]]; then
  echo "Error: Missing required parameters"
  echo "Usage: $0 --python PYTHON --script-dir SCRIPT_DIR --working-dir WORKING_DIR --input-data INPUT_DATA --gemini-run-id GEMINI_RUN_ID --output-path OUTPUT_PATH"
  exit 1
fi

# Create .datacommons directory if it doesn't exist
mkdir -p "${WORKING_DIR}/.datacommons"

# Extract output directory for backup purposes
OUTPUT_DIR=$(dirname "${OUTPUT_PATH}")

# Define log file paths (persistent files that Gemini can read)
PROCESSOR_LOG="${WORKING_DIR}/.datacommons/processor.log"
BACKUP_LOG="${WORKING_DIR}/.datacommons/backup.log"
# Keep CSV column ordering predictable across runs when importing multiple files.
OUTPUT_COLUMNS="observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor"
# TODO : Add existing_statvar_mcf, existing_schema_mcf support
# Run statvar processor with output going to persistent log
# Keep constant-value columns because custom DC imports read the CSV directly and skip the TMCF.
echo "Running statvar processor..."
"${PYTHON_INTERPRETER}" "${SCRIPT_DIR}/statvar_importer/stat_var_processor.py" \
  --input_data="${INPUT_DATA}" \
  --pv_map="${WORKING_DIR}/${OUTPUT_PATH}_pvmap.csv" \
  --config_file="${WORKING_DIR}/${OUTPUT_PATH}_metadata.csv" \
  --generate_statvar_name=True \
  --skip_constant_csv_columns=False \
  --output_columns="${OUTPUT_COLUMNS}" \
  --output_counters="${WORKING_DIR}/.datacommons/output_counters.csv" \
  --output_path="${WORKING_DIR}/${OUTPUT_PATH}" > "${PROCESSOR_LOG}" 2>&1

# Capture the processor exit code
PROCESSOR_EXIT_CODE=${PIPESTATUS[0]}

# Run backup script silently (redirect output to backup log)
echo "Backing up run data..."
"${PYTHON_INTERPRETER}" "${SCRIPT_DIR}/agentic_import/backup_processor_run.py" \
  --working_dir="${WORKING_DIR}" \
  --gemini_run_id="${GEMINI_RUN_ID}" \
  --backup_files="${OUTPUT_DIR}" \
  --backup_files="${PROCESSOR_LOG}" \
  --backup_files="${WORKING_DIR}/.datacommons/output_counters.csv" > "${BACKUP_LOG}" 2>&1

# Check the processor exit code and exit accordingly
if [ ${PROCESSOR_EXIT_CODE} -ne 0 ]; then
    echo "Statvar processor failed with exit code: ${PROCESSOR_EXIT_CODE}"
    exit ${PROCESSOR_EXIT_CODE}
fi

echo "Statvar processor completed successfully"
echo "Statvar processor logs available at: ${PROCESSOR_LOG}"
