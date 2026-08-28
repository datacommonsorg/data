#!/bin/bash

for FILE in gcs_output/input_files/ACCIDENT_*.csv; do
    YEAR=$(basename "$FILE" | cut -d'_' -f2 | cut -d'.' -f1)
    python3 ../../../tools/statvar_importer/stat_var_processor.py \
        --input_data="$FILE" \
        --pv_map=fars_crash_pvmap.csv \
        --config_file=fars_crash_metadata.csv \
        --output_path="gcs_output/output/fars_crash_${YEAR}" \
        --output_counters="counters/fars_crash_${YEAR}_counters.csv" \
        --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
done
