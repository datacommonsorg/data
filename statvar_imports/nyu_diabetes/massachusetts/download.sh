#!/bin/bash

set -euo pipefail  # Exit on error

echo "Step 1: Copying CSV files from GCS..."
mkdir -p input_files
gsutil cp gs://unresolved_mcf/nyu_diabetes/massachusetts/input_files/Massachusetts-Diabetes-data.csv input_files/

echo "Preprocessing done. StatVar processing will now continue as per manifest."
