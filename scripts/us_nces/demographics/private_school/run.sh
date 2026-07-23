#!/bin/bash

# 1. Get the absolute path to the 'private_school' directory
BASE_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# 3. Create the actual data storage folder in the base directory
mkdir -p "$BASE_DIR/gcs_folder/input_files"

# 4. Download files
gcloud storage cp --recursive "gs://unresolved_mcf/us_nces/demographics/private_school/semi_automation_input_files/*" "$BASE_DIR/gcs_folder/input_files/"

# 5. Run the process
cd "$BASE_DIR"
python process.py --stats
