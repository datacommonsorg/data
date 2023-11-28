#!/bin/bash
# Script used to generate TMCF/CSV/MCF for EPA GHGRP

pushd ../../../
python3 -m venv .env
source .env/bin/activate
pip3 install -r requirements_all.txt -q
popd

# Generate schema to import_data/
python3 -m gas
python3 -m sources

# Download and process data, output CSV written to import_data/
python3 -m process
