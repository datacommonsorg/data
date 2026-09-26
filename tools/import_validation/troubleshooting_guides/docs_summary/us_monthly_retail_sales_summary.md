# Google Doc: USMonthlyRetailsales Summary

*   **Original URL:** https://docs.google.com/document/d/1mVoeHRkdlnPvTpu-IMee-6d2GQ-htlLDRP2ZYdGW04w/edit
*   **Purpose/Overview:** This document outlines a validation failure for the `USMonthlyRetailsales` dataset on April 14, 2026.
*   **Problem Description:** The import failed during validation due to 4 (0.01%) deleted records.
*   **Root Causes:** The StatVar processor incorrectly treated industry category codes (NAICS) in the source file as financial values and attempted to multiply them by 1,000,000 (standard conversion to USD), which triggered validation inconsistencies.
*   **Resolutions/Findings:** 
    *   The StatVar processor logic was updated to ignore NAICS industry codes and avoid converting non-financial records.
    *   The pipeline was then re-run to confirm clean validation.
