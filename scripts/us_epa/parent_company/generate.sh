#!/bin/bash

# Download the existing Facility dcids.
python3 download_existing_facilities.py

# Download the tables to tmp_data/
python3 download_parent_companies.py --companies_table_name=V_PARENT_COMPANY_INFO

# Process them from tmp_data/ and produce tmcf/csv in output/
python3 process_parent_company.py