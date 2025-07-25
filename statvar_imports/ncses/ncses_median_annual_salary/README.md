# NCSES Median Annual Salary Autorefresh

1. Import Overview
    - Source URL: [https://ncses.nsf.gov/pubs/nsf23306#section13069](https://ncses.nsf.gov/pubs/nsf23306#section13069)
    - Import Type: What kind of import is this (e.g., API, manual upload, database dump)?
    - Source Data Availability: The data is available for every 2 years (2017,19,21,23)
    - Release Frequency: P2Y
    - how to download data: Download script (download.py)

2. Autorefresh Type

    - Fully Autorefresh: Cloud Run job: `30 05 13,27 * *`.

4. Script Execution Details
    - download.py - downloads the data from source and stores it in input_files as a `.xlsx` fileformat
    - statvar_processor.py - Using a statvar script to process the data.
    - Using common pvmap and metadata for the import.
