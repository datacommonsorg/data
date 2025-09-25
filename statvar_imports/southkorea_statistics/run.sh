#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gcs_path>"
    exit 1
fi

GCS_PATH=$1
DESTINATION_DIR="source_files"

mkdir -p "${DESTINATION_DIR}"
gsutil -m cp "${GCS_PATH}*.csv" "${DESTINATION_DIR}/"