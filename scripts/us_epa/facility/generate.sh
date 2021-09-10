#!/bin/bash
# Script used to generate TMCF/CSV for EPA facilities

# TODO: Add command-line to generate crosswalk.csv

# Download the tables to data/
python3 download_efservice.py --epa_table_name=V_GHG_EMITTER_FACILITIES
python3 download_efservice.py --epa_table_name=V_GHG_SUPPLIER_FACILITIES
python3 download_efservice.py --epa_table_name=V_GHG_INJECTION_FACILITIES

# Process them from data/ and produce tmcf/csv in output/
python3 process_facility.py
