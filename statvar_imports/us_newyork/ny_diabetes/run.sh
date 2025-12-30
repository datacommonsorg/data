#!/bin/bash

set -e  # Exit on error

echo "Step 1: Copying SVI files from GCS..."
mkdir -p input_files
gsutil cp gs://unresolved_mcf/nyu_diabetes/adult_diabetes/input_files/*.csv input_files/

echo "Preprocessing done. StatVar processing will now continue as per manifest."

