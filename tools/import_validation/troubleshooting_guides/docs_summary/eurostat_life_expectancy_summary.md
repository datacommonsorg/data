# Google Doc: EurostatData_LifeExpectancy Summary

*   **Original URL:** https://docs.google.com/document/d/1h4ETCMddDTWPCCZnE8OaHNYKFAH2WHtUX9tGCxV5caY/edit
*   **Purpose/Overview:** This document covers the failure analysis for the `EurostatData_LifeExpectancy` import pipeline on March 19, 2026.
*   **Problem Description:** The import pipeline failed due to 53,445 lint errors and 1.15% deleted records.
*   **Root Causes:** Eurostat adjusted its data retention policy and stopped publishing historical life expectancy data before the year 2000, resulting in the deletion of all pre-2000 records from the source.
*   **Resolutions/Findings:** 
    *   To retain the historical data, the pipeline was updated to run with the deleted rows historical dataset from CNS (Content Native Storage).
    *   The validation threshold configurations were updated to allow the import to successfully complete with these changes.
