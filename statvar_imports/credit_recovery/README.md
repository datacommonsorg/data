# US Urban Education School Autorefresh: Credit Recovery Data Import

This directory contains the scripts and data for importing credit recovery statistics from the Civil Rights Data Collection (CRDC).

## Overview

The import process involves the following steps:

1.  **Downloading Data**: The `download.py` script fetches CRDC data archives from the official ED.gov website for the years 2012-2025. It then extracts and organizes the relevant files, specifically those related to "credit recovery," into the `files/credit` directory.

2.  **Processing Raw Data**: The `creditprocess.py` script reads the raw data files from `files/credit`. It cleans the data by converting "Yes"/"No" values to 1/0, extracts the academic year from the filenames, and saves the processed data into the `input_credit` directory as CSV files.

3.  **Generating Final Output**: The processed files in `input_credit` are then used to generate the final `output/output_credit.csv` file, which contains the aggregated statistics in a format suitable for import.

## How to Run

To run the import process, execute the scripts in the following order:

1.  **Download the data**:
    ```bash
    python3 download.py
    ```

2.  **Process the raw data**:
    ```bash
    python3 creditprocess.py
    ```

## File Structure

-   `download.py`: Script to download and organize the raw data files.
-   `creditprocess.py`: Script to process the raw data and prepare it for the final import.
-   `files/credit/`: Directory containing the raw, downloaded credit recovery data files.
-   `input_credit/`: Directory containing the processed, cleaned CSV files.
-   `output_pro/`: Directory containing the final, aggregated output files for import.
    -   `output.csv`: The main data file with aggregated statistics.
    -   `output.tmcf`: Template MCF file for the import.
    -   `output_stat_vars.mcf`: Statistical variable definitions.
    -   `output_stat_vars_schema.mcf`: Schema for the statistical variables.
-   `metadata.csv`: Contains metadata about the import.
-   `pvmap.csv`: Maps property values for the import.

## Notes

-   The `download.py` script requires the `download_util_script.py` utility, which is expected to be in the `../../util` directory.
-   The scripts are designed to be run from the current directory (`data/statvar_imports/credit_recovery`).
