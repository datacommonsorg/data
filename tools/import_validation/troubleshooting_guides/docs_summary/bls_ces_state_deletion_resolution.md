# Google Doc: BLS_CES_State Deletion Resolution Summary

*   **Original URL:** https://docs.google.com/document/d/1QK9pMoSFR7STb78aFgN_NOupcJzU_IdWp4tyIvzrwis/edit
*   **Purpose/Overview:** This document outlines the resolution plan for a validation failure in the `BLS_CES_State` data import on April 20, 2026.
*   **Problem Description:** The import process failed because 4.57% (33,120 records) of the data points were deleted, which exceeded the default 0% threshold.
*   **Root Causes:** The Bureau of Labor Statistics (BLS) announced official reductions and eliminations of several series data points starting with the release of January 2026 data as part of their annual benchmarking and sample review.
*   **Resolutions/Findings:** 
    *   Since these deletions are official source-side changes, the deleted records cannot be recovered.
    *   To resolve the import failure, the deleted data was preserved by extracting and storing it in a historical file, uploading it to Content Native Storage, and adjusting the validation settings to allow the pipeline to complete.
