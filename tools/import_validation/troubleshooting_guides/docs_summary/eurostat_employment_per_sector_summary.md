# Google Doc: EurostatData_Employment_Per_Sector Summary

*   **Original URL:** https://docs.google.com/document/d/1CPyqi9DBjv0t4eWanNYMRfJTIGjhubN6Op2Sao5S-9Y/edit
*   **Purpose/Overview:** This document analyzes an import failure for the `EurostatData_Employment_Per_Sector` dataset on February 16, 2026.
*   **Problem Description:** The process failed because it found 6,645 deleted records (1.39% of the total), which exceeded the allowed 0% threshold for deletions.
*   **Root Causes:** The failure was caused by missing source data for the years 1995–1999 across 92 NUTS/IDs. The data was deleted from the official Eurostat source and is not expected to be restored.
*   **Resolutions/Findings:** To resolve the validation error, the document recommends preserving the missing data by identifying it through a comparison with the previous production version, storing it in a historical file, and uploading it to Content Native Storage.
