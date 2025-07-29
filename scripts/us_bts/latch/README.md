# USBTS Tract Household Transportation Data Processing

## Overview

This project provides a semi-automated pipeline for downloading and processing the U.S. Bureau of Transportation Statistics (USBTS) LATCH (Local Area Transportation Characteristics for Households) dataset. It is designed to handle data from different years, currently supporting 2009 and 2017.

The scripts perform the following actions:
1.  **Download:** Fetches the LATCH dataset directly from the source URLs specified in the configuration.
2.  **Process:** Cleans and transforms the raw data into a consistent format, generating final CSV, MCF, and TMCF files for import into the Data Commons knowledge graph.

## A Note on Data Source URLs

This import is considered semi-automated due to the nature of the data source. The URLs for the LATCH dataset are not predictable and may change when new data is released. As a result, the `import_configs.json` file may need to be manually updated to point to the latest data files.

## Prerequisites

- Python 3.x
- The following Python libraries are required:
  - `pandas`
  - `numpy`
  - `requests`
  - `absl-py`

## Setup

1.  **Install Dependencies:**
    Install the required Python libraries using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Scripts

Follow these steps to download and process the data:

1.  **Download the Data:**
    Execute the `download_script.py` script to fetch the raw data files from the URLs specified in `import_configs.json`. The files will be saved in the `input_files` directory.

    ```bash
    python3 download_script.py
    ```

2.  **Process the Data:**
    After the download is complete, run the `process.py` script to clean, transform, and format the data. This script will generate the final output files in the `output` directory.

    ```bash
    python3 process.py
    ```

## Project Structure

```
├── constants.py                # Defines constants used across the project
├── download_script.py          # Main script to download raw data
├── download.py                 # Utility module for downloading files
├── import_configs.json         # Configuration for data import with source URLs
├── input_urls_config.json      # (Legacy) Contains URLs for the input data
├── process.py                  # Script to process the raw data
├── statvar_dcid_generator.py   # Generates StatisticalVariable DCIDs
├── output/                     # Directory for processed output files
│   ├── us_transportation_household.csv
│   ├── us_transportation_household.mcf
│   └── us_transportation_household.tmcf
├── test_data/                  # Contains data for testing purposes
└── README.md                   # This file
```

## Input Data

The input data is sourced from the Bureau of Transportation Statistics (BTS) LATCH dataset. The URLs for the specific data files are defined in `import_configs.json`. The `download_script.py` script handles the download and storage of these files.

## Output

The processing script generates the following files in the `output/` directory:

-   `us_transportation_household.csv`: The main cleaned and processed data file, split into multiple parts.
-   `us_transportation_household.mcf`: The StatisticalVariable nodes for the dataset.
-   `us_transportation_household.tmcf`: The template MCF for importing the CSV data into Data Commons.

## Testing

To verify the functionality of the processing script, run the `process_test.py` script:

```bash
python3 process_test.py
```
This will run tests against the data in the `test_data` directory and ensure the output is as expected.