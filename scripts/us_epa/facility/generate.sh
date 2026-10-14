#!/bin/bash
# Script used to generate TMCF/CSV for EPA facilities
set -e

# Download the facility table and generate crosswalks in tmp_data/
python3 download_efservice.py --epa_table_name=PUB_DIM_FACILITY

# Process them from tmp_data/ and produce tmcf/csv in output/
python3 process_facility.py
