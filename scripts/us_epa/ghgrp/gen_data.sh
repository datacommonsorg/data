#!/bin/bash
# Script used to generate TMCF/CSV/MCF for EPA GHGRP

pushd ../../../
echo "Configuring venv...."
python3 -m venv .env
source .env/bin/activate
#pip3 install -r requirements.txt -q
popd

# Generate schema to import_data/
#python3 -m gas
echo "Executing gas module..."
/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_epa/ghgrp/.env/bin/python3 -m gas
#python3 -m sources
echo "Executing sources module..."

/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_epa/ghgrp/.env/bin/python3 -m sources
# Download and process data, output CSV written to import_data/
#python3 -m process
echo "Executing process module..."

/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_epa/ghgrp/.env/bin/python3 -m process

echo "Execution Completed..."
