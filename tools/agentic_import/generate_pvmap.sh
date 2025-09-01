#!/bin/bash

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Save original directory at the start
ORIGINAL_DIR="$(pwd)"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the root directory of the data repository
DATA_REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Function to setup Python environment
function setup_python_environment {    
    cd "$DATA_REPO_ROOT"
    
    # Always run run_tests.sh -r to setup/update Python environment
    echo "Setting up Python environment..."
    ./run_tests.sh -r
    
    # Activate the environment
    echo "Activating Python virtual environment..."
    source .env/bin/activate 
}

# Function to run the PV map generator
function run_pvmap_generator {
    # Ensure we're back in the original directory before running the generator
    cd "$ORIGINAL_DIR"
    echo "Running PV Map generator from: $(pwd)"
    python3 "$SCRIPT_DIR/pvmap_generator.py" "$@"
}

setup_python_environment
mkdir -p "$ORIGINAL_DIR/.datacommons"
run_pvmap_generator "$@"
echo "PV Map generation completed."