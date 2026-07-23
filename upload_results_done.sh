#!/bin/bash
BASE_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/abhishek_data"
GCS_BASE="gs://unresolved_mcf/Eurostat/sdmx_done"

for dataset_dir in "$BASE_DIR"/*; do
  if [ -d "$dataset_dir" ]; then
    dataset_name=$(basename "$dataset_dir")
    results_dir="$dataset_dir/efficacy_results"
    
    if [ -d "$results_dir" ]; then
      echo "Uploading results for $dataset_name..."
      gcloud storage cp --recursive "$results_dir" "$GCS_BASE/$dataset_name/"
    fi
  fi
done
