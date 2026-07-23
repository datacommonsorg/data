#!/bin/bash
REVIEWED_DIR="undata/DESA/output/reviewed"
for dir in "${REVIEWED_DIR}"/*/; do
  DATASET_NAME=$(basename "${dir}")
  
  echo "Moving files for ${DATASET_NAME}..."
  
  [ -f "${REVIEWED_DIR}/${DATASET_NAME}.csv" ] && mv "${REVIEWED_DIR}/${DATASET_NAME}.csv" "${dir}output.csv"
  [ -f "${REVIEWED_DIR}/${DATASET_NAME}.tmcf" ] && mv "${REVIEWED_DIR}/${DATASET_NAME}.tmcf" "${dir}output.tmcf"
  [ -f "${REVIEWED_DIR}/${DATASET_NAME}_stat_vars.mcf" ] && mv "${REVIEWED_DIR}/${DATASET_NAME}_stat_vars.mcf" "${dir}output_stat_vars.mcf"
  [ -f "${REVIEWED_DIR}/${DATASET_NAME}_stat_vars_schema.mcf" ] && mv "${REVIEWED_DIR}/${DATASET_NAME}_stat_vars_schema.mcf" "${dir}output_stat_vars_schema.mcf"
done
