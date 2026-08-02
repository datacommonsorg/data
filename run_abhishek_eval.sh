#!/bin/bash

BASE_DIR="/usr/local/google/home/nehil/datacommons/import/git/data/abhishek_data"
TOOL_SCRIPT="/usr/local/google/home/nehil/datacommons/import/git/data/tools/agent_efficacy/calculate_efficacy.py"

source /usr/local/google/home/nehil/datacommons/import/git/data/venv/bin/activate

for dataset_dir in "$BASE_DIR"/*; do
  if [ -d "$dataset_dir" ]; then
    dataset_name=$(basename "$dataset_dir")
    sample_dir="$dataset_dir/sample_output"
    
    test_file="$sample_dir/output_pvmap.csv"
    gold_file="$sample_dir/output_pvmap_cleaned.csv"
    
    if [ -f "$test_file" ] && [ -f "$gold_file" ]; then
      echo "Processing dataset: $dataset_name"
      output_dir="$dataset_dir/efficacy_results"
      mkdir -p "$output_dir"
      
      python3 "$TOOL_SCRIPT" \
        --test "$dataset_dir" \
        --output "$output_dir" \
        --dataset_id "$dataset_name"
    else
      echo "Skipping dataset: $dataset_name (Missing required CSV files)"
    fi
  fi
done
