# Import for EPA's GHGRP data

This directory contains scripts to download and import the US EPA's Greenhouse
Gas Reporting Program data from
#https://www.epa.gov/sites/default/files/2020-11/2019_data_summary_spreadsheets.zip
https://www.epa.gov/system/files/other-files/2022-10/2021_data_summary_spreadsheets.zip

## Resolution

We use the provided "crosswalk" between facilities and EIA, and assume that reporting facilities
were included in the import from [EPA GHG facility import](../facility/README.md)

## Generating and Validating Artifacts

## Moved confiuration changes to config.txt

 Moved frequent  config related changes to config.txt

DOWNLOAD_URI = Download URL from EPA
Latest URL: https://www.epa.gov/system/files/other-files/2022-10/2021_data_summary_spreadsheets.zip
CROSSWALK_URI = Crosswalk URL
Latest Cross walk URL: https://www.epa.gov/system/files/documents/2022-04/ghgrp_oris_power_plant_crosswalk_12_13_21.xlsx
YEAR_DATA_FILENAME = Downloaded_Folder_Name/Original File name
Start_Year_Range = Start range
End_Year_Range = Till what year update is available
End_Year_Range changed from 2020 to 2022

1. To download crosswalks, tables and regenerate the TMCF/CSV/MCF, run:

      ```
      ./gen_data.sh
      ```

2. To run unit tests:

      ```
      python3 -m unittest discover -v -s ../ -p "*_test.py"
      ```
      or
      ```
      cd ../../../
      ./run_tests.sh -p scripts/us_epa/ghgrp
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
            "Existence_NumChecks": "4362098",
            "Existence_NumDcCalls": "29",
            "NumNodeSuccesses": "396460",
            "NumPVSuccesses": "3171680",
            "NumRowSuccesses": "396460"
          }
        }
      }
    ```

