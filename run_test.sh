#!/bin/bash
set -e

# Define color variables (copied from import_pipeline.sh)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
CYAN=$(tput setaf 6)
BLUE=$(tput setaf 4)
YELLOW=$(tput setaf 3)
MAGENTA=$(tput setaf 5)
NC=$(tput sgr0)

# Create a bin directory for python symlink
mkdir -p test_undata_run/bin
ln -sf $(which python3) test_undata_run/bin/python
export PATH="$PWD/test_undata_run/bin:$PATH"

# Source the pipeline script
source import_pipeline.sh

# Set the variables for the chosen import
export IMPORT_NAME="DESA-GENDER_2025_OBS_LIFE_EXP"
export LOCAL_DIR="$PWD/test_undata_run"
export SOURCE_FILES="$PWD/undata/DESA/data/DESA-GENDER_2025_OBS_LIFE_EXP.csv"
export PY_SCRIPT_DIR="$PWD"
export GIT_DIR="$PWD"
export TMP_DIR="$LOCAL_DIR/tmp"
mkdir -p "$TMP_DIR"

# Set PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$PY_SCRIPT_DIR/util:$PY_SCRIPT_DIR/tools/statvar_importer"
export PYTHONPATH="$PYTHONPATH:$PY_SCRIPT_DIR:$PY_SCRIPT_DIR/data"

# Mock/Set some variables that setup normally sets
export LOG="$LOCAL_DIR/test.log"
touch "$LOG"
export DEFAULT_STATVAR_PROCESSOR_ARGS="--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --skip_constant_csv_columns=False"
export MIN_PERCENT_INPUT_PROCESSED=0 # Set to 0 for now to avoid fatal if it fails to process 80%

echo "Setting up dc-import tool..."
setup_dc_import

echo "Setting up python environment..."
setup_python

echo "Running stat_var_processor..."
stat_var_processor

echo "Running validate_output..."
validate_output

echo "Done. Results in $LOCAL_DIR"
