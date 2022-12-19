#!/bin/bash

sh/download_data.sh

# Process the data
python3 generate_schema_and_tmcf.py
# process_data.py depends on artifacts produced by generate_schema_and_tmcf.py
python3 process_data.py
