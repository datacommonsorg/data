# World Bank Datasets

- source: https://data.worldbank.org

- how to download data: Auto download of data by using python script(datasets.py).

- type of place: Country.

- statvars: All Type

- years: 1960 to 2050

-copyright year: 2024

### How to run:
"""Processes WB datasets.

update september 2024:
To run all processing methods , please do not pass the mode 
Run: python3 datasets.py

Or If required to check issue in any individual process follow all the steps as below:

Supports the following tasks:

============================

fetch_datasets: Fetches WB dataset lists and resources and writes them to 'output/wb-datasets.csv'

Run: python3 datasets.py --mode=fetch_datasets

============================

download_datasets: Downloads datasets listed in 'output/wb-datasets.csv' to the 'output/downloads' folder.

Run: python3 datasets.py --mode=download_datasets

============================

write_wb_codes: Extracts World Bank indicator codes (and related information) from files downloaded in the  'output/downloads' folder to 'output/wb-codes.csv'.

It only operates on files that are named '*_CSV.zip'.

Run: python3 datasets.py --mode=write_wb_codes

============================

load_stat_vars: Loads stat vars from a mapping file specified via the `stat_vars_file` flag.

Use this for debugging to ensure that the mappings load correctly and fix any errors logged by this operation.

Run: python3 datasets.py --mode=load_stat_vars --stat_vars_file=/path/to/statvars.csv

See `sample-svs.csv` for a sample mappings file.

============================

write_observations: Extracts observations from files downloaded in the 'output/downloads' folder and saves them to CSVs in the 'output/observations' folder.

The stat vars file to be used for mappings should be specified using the `stat_vars_file' flag.

It only operates on files that are named '*_CSV.zip'.

Run: python3 datasets.py --mode=write_observations --stat_vars_file=/path/to/statvars.csv
"""

