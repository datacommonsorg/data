#!/bin/bash
# Script used to generate TMCF/CSV for EPA facilities

# Download all the excels and compute crosswalk to tmp_data/
python3 ../ghgrp/download.py

# Download the tables to tmp_data/
python3 download_efservice.py --epa_table_name=V_GHG_EMITTER_FACILITIES
python3 download_efservice.py --epa_table_name=V_GHG_SUPPLIER_FACILITIES
python3 download_efservice.py --epa_table_name=V_GHG_INJECTION_FACILITIES

# Process them from tmp_data/ and produce tmcf/csv in output/
python3 process_facility.py
