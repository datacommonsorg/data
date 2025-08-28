# NCSES Demographics SEH Autorefresh

1. Import Overview
    - Source URL: [https://ncses.nsf.gov/pubs/nsf25316](https://ncses.nsf.gov/pubs/nsf25316)
    - Import Type: API automated download.
    - Source Data Availability: The data is available every year(actively from 2021).
    - Release Frequency: P1Y
    - how to download data: Download script (download.py)

2. Autorefresh Type

    - Fully Autorefresh: Cloud Run job: `30 05 12,28 * *`.

3. Script Execution Details
    - download.py - downloads the data from source and stores it in input_files as a `.xlsx` fileformat
    - statvar_processor.py - Using a statvar script to process the data.
    - Using common pvmap and metadata for the import.

### How to run
 `python3 download.py`

 `python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/nsf*.xlsx --pv_map=ncses_demographics_seh_import_pv_map.csv --config_file=ncses_demographics_seh_import_metadata.csv  --statvar_dcid_remap_csv=ncses_demographics_seh_import_remap.csv --output_path=output/ncses_demographics_seh_import`