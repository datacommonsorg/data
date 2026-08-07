# Google Doc: WorldBankDatasets Summary

*   **Original URL:** https://docs.google.com/document/d/1ExMv5_J4vSEY1OVwWLoXbvnH1ltjRsfcBjUqSyw6uXo/edit
*   **Purpose/Overview:** This document outlines failures in the `WorldBankDatasets` auto-refresh pipeline on August 25, 2025.
*   **Problem Description:** The import pipeline failed due to approximately 1.3 million lint errors and 18,398 deleted data points, exceeding the threshold.
*   **Root Causes:** 
    *   **Deletions:** The source data did not contain the observations.
    *   **Lint Errors:** Aggregated regional groupings and place names in the source data used invalid DCIDs (e.g. Channel Islands as `CHI` and Kosovo as `XKX`) that did not exist in Data Commons.
*   **Resolutions/Findings:** 
    *   Resolved the lint errors by mapping invalid place DCIDs using `places.csv` and `skip_places.csv` filters.
    *   Preserved the deleted data points by writing them to a historical `deleted_rows.csv` file, uploading it to Content Native Storage, and configuring it to skip errors during future pipeline runs.
