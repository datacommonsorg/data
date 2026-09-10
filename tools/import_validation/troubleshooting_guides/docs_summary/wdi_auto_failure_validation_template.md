# Google Doc: World Development Indicators Auto-Failure Validation Summary

*   **Original URL:** https://docs.google.com/document/d/1PyBmcN-1C_p9y-ML93eaBFyspg1XD5zwkT7EqeTsQsI/edit
*   **Purpose/Overview:** Used as a reference template for validation failure analysis, documenting a failure in the WDI pipeline on December 23, 2025.
*   **Problem Description:** The pipeline failed due to 1,011 validation errors (deletions) and 908 lint errors.
*   **Root Causes:** 
    *   **Syria Deletions:** Data for Syria was missing from the source folder due to a change in the source layout.
    *   **Kosovo Code Mismatch:** The source data used the 3-letter code `XKX` for Kosovo, which failed validation because Data Commons uses the `XKS` code.
    *   **Channel Islands Mismatch:** The source data used `CHI` which did not match the Data Commons DCID `ChannelIslands`.
*   **Resolutions/Findings:** 
    *   Updated the `latest_version.txt` configuration file to point to the latest source folder structure.
    *   Updated the `worldbank.py` script to map country code `XKX` to `XKS` and `country/CHI` to `ChannelIslands` to resolve lint validation failures.
