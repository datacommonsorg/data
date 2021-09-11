# Import for EPA's GHGRP data

This directory contains scripts to download and import the US EPA's Greenhouse
Gas Reporting Program data from
https://www.epa.gov/sites/default/files/2020-11/2019_data_summary_spreadsheets.zip

## Resolution

We use the provided "crosswalk" between facilities and EIA, and assume that reporting facilities
were included in the import from [EPA GHG facility import](../facility/README.md)

## Generating and Validating Artifacts

1. To download crosswalks, tables and regenerate the TMCF/CSV/MCF, run:

      ```
      ./gen_data.sh
      ```

2. To run unit tests:

      ```
      python3 -m unittest discover -v -s ../ -p "*_test.py"
      ```

3. To validate the import, run the [dc-import](https://github.com/datacommonsorg/import#using-import-tool) tool as:

    ```
    dc-import lint import_data/*
    ```

    This produced the following report:

    ```
      {
        "counterSet": {
          "counters": {
            "Existence_NumChecks": "4362086",
            "Existence_NumDcCalls": "28",
            "NumNodeSuccesses": "396460",
            "NumPVSuccesses": "3171680",
            "NumRowSuccesses": "396460"
          }
        }
      }
    ```

