#!/bin/bash
# Activate the existing virtual environment
source /usr/local/google/home/nehil/datacommons/import/git/data/venv/bin/activate

# Define an array of 10 dataset names
DATASETS=(
"SDG_q4-2025_OBS_EG_ACS_ELEC"
"SDG_q4-2025_OBS_EG_EGY_CLEAN"
"SDG_q4-2025_OBS_EG_EGY_RNEW"
"SDG_q4-2025_OBS_EG_FEC_RNEW"
"SDG_q4-2025_OBS_EG_IFF_RANDN"
"SDG_q4-2025_OBS_EN_ATM_CO2"
"SDG_q4-2025_OBS_EN_ATM_PM25"
"SDG_q4-2025_OBS_EN_LKRV_PWAN"
"SDG_q4-2025_OBS_EN_LKRV_SWAN"
"SDG_q4-2025_OBS_EN_MAR_BEALIT_BV"
)

for DATASET_NAME in "${DATASETS[@]}"; do
    echo "Processing ${DATASET_NAME}..."
    DATASET_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/deterministic/${DATASET_NAME}"

    # Ensure validation output directory exists
    mkdir -p "${DATASET_DIR}/validation"

    # Run the statvar processor
    python3 /usr/local/google/home/nehil/datacommons/import/git/data/tools/statvar_importer/stat_var_processor.py \
      --input_data="${DATASET_DIR}/input/data.csv" \
      --config_file="${DATASET_DIR}/deterministic_metadata.csv" \
      --pv_map="${DATASET_DIR}/deterministic_pvmap.csv" \
      --places_resolved_csv="/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/all_places.csv" \
      --output_path="${DATASET_DIR}/output" \
      --output_counters="${DATASET_DIR}/validation/statvar_processor_counters.csv"
done
