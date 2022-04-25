#!/bin/bash

# Download the existing Facility dcids.
python3 download_existing_facilities.py

# Download the tables to tmp_data/
python3 download_parent_companies.py --companies_table_name=V_PARENT_COMPANY_INFO

# Pre-Process the company names to resolve to unique ID mappings.
# The input is expected from tmp_data/ and the output produced also goes to
# /tmp.
python3 pre_process.py

# Process them from tmp_data/ and produce tmcf/csv in output/
python3 process_parent_company.py
