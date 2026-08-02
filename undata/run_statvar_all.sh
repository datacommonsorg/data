#!/bin/bash
# Activate the existing virtual environment
source venv/bin/activate

REVIEWED_DIR="${1:-undata/DESA/output/reviewed}"
DATA_DIR="undata/DESA/data"

# Extract the directory name for GCS upload path
DIR_NAME=$(basename "${REVIEWED_DIR}")

# Iterate over all directories in the reviewed folder
for dir in "${REVIEWED_DIR}"/*/; do
  # Extract dataset name (remove trailing slash and path)
  DATASET_NAME=$(basename "${dir}")
  
  # Skip if it's not a directory (though the glob should handle it)
  [ -d "${dir}" ] || continue
  
  echo "Processing dataset: ${DATASET_NAME}..."
  
  DATASET_DIR="${REVIEWED_DIR}/${DATASET_NAME}"
  VALIDATION_DIR="${DATASET_DIR}/validation"

  # Check if validation folder is empty
  if [ -d "$VALIDATION_DIR" ] && [ "$(ls -A "$VALIDATION_DIR" 2>/dev/null)" ]; then
    echo "Skipping ${DATASET_NAME}: validation folder is not empty."
    continue
  fi

  INPUT_CSV="${DATA_DIR}/${DATASET_NAME}.csv"
  
  if [ ! -f "${INPUT_CSV}" ]; then
    echo "Warning: Input CSV not found for ${DATASET_NAME} at ${INPUT_CSV}. Skipping."
    continue
  fi
  
  # Run the statvar processor
  ./venv/bin/python tools/statvar_importer/stat_var_processor.py \
    --input_data="${INPUT_CSV}" \
    --config_file="${DATASET_DIR}/output_metadata.csv" \
    --pv_map="${DATASET_DIR}/output_pvmap.csv" \
    --output_path="${DATASET_DIR}/output" \
    --places_resolved_csv=/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/all_places.csv \
    --output_counters="${DATASET_DIR}/validation/statvar_processor_counters.csv"
  
  echo "Completed ${DATASET_NAME}."
done

echo "Uploading all processed files to GCS..."
gcloud storage cp -r "${REVIEWED_DIR}/"* "gs://undata/desa-gender/2025/transcoded/output/${DIR_NAME}/"
