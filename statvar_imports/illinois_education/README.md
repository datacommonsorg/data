# Illinois State Board of Education (ISBE) Report Card Data Processing

## Overview

This project provides a semi-automated pipeline for downloading and processing the Illinois State Report Card data from the Illinois State Board of Education (ISBE). It is designed to handle data from different school years.

The scripts perform the following actions:
1.  **Download:** Fetches the dataset directly from the source URLs specified in the configuration.
2.  **Process:** Cleans and transforms the raw data into a consistent format, generating final CSV, MCF, and TMCF files for import into the Data Commons knowledge graph.

## A Note on Data Source URLs

This import is considered semi-automated due to the nature of the data source. The URLs for the dataset may change when new data is released. As a result, the `import_configs.json` file may need to be manually updated to point to the latest data files.

## Autorefresh Information

This import is considered semi-automated because the data source URLs are not stable and require manual updates for new releases. To refresh the data, you will need to:

1.  **Check for New Data:** Visit the [ISBE Report Card Data website](https://www.isbe.net/Pages/Illinois-State-Report-Card-Data.aspx) to check for new data releases.
2.  **Update Configuration:** If new data is available, update the `import_configs.json` file with the new URLs and corresponding year information.
3.  **Run Scripts:** Execute the download and processing scripts as outlined below.

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
├── download_script.py          # Main script to download raw data
├── download.py                 # Utility module for downloading files
├── import_configs.json         # Configuration for data import with source URLs
├── process.py                  # Script to process the raw data
├── output/                     # Directory for multiple processed output files
│   ├── illinois_education.csv
│   ├── illinois_education.mcf
│   └── illinois_education.tmcf
├── test_data/                  # Contains data for testing purposes
└── README.md                   # This file
```

## Input Data

The input data is sourced from the [Illinois State Board of Education (ISBE)](https://www.isbe.net/Pages/Illinois-State-Report-Card-Data.aspx). The URLs for the specific data files are defined in `import_configs.json`. The `download_script.py` script handles the download and storage of these files.

## Output

The processing script generates the following files in the `output/` directory:

-   `illinois_education_output.csv`: The main cleaned and processed data file.
-   `schema_common.mcf`: The StatisticalVariable nodes for the dataset.
-   `output.tmcf`: The template MCF for importing the CSV data into Data Commons.


