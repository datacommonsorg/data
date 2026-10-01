# Google Doc: EIA_SEDS Summary

*   **Original URL:** https://docs.google.com/document/d/1Kvhz-7AaWpaxSvSN1wHDP75-3CVXTfZT7dffBgZNTaY/edit
*   **Purpose/Overview:** This document describes the validation failure of the `EIA_SEDS` data import on April 20, 2026.
*   **Problem Description:** The import failed due to 1,248 (0.05%) deleted records and 56 missing reference warnings.
*   **Root Causes:** 
    *   **Deletions:** The source data removed zero-value placeholders that were not part of the NL Statistical Variables.
    *   **Missing References:** The source introduced new Statistical Variables that were not defined in the Data Commons schema.
*   **Resolutions/Findings:** 
    *   Acknowledged the deletions by updating `latest_version.txt`.
    *   Created and merged a Change List (CL) to add the definitions for the 56 new Statistical Variables in Data Commons, then ran a forced update.
