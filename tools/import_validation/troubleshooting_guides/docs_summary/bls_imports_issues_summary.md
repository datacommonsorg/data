# Google Doc: BLS Imports Issues Summary

*   **Original URL:** https://docs.google.com/document/d/1bQbwKMVPtcehUZ3zI3r2kGlidMiE6UjEN9faKlJgtUs/edit
*   **Purpose/Overview:** This document provides a general overview of multiple common issues and fixes across various BLS (Bureau of Labor Statistics) data imports (CES, CPI_Category, CES_State, etc.).
*   **Problem Description:** Multiple BLS pipelines failed due to outdated files, missing references, and blocked automated downloads.
*   **Root Causes & Fixes:** 
    *   **Outdated latest_version.txt:** The Cloud Batch run date was newer than the version indicated in the `latest_version.txt` file, causing false deletion detections. Fixed by manually updating the `latest_version.txt` configuration.
    *   **Dependency on Production Schema Releases:** New Statistical Variables (SVs) added to the schema caused missing reference errors until the production release was finalized. Resolved by updating the pipeline to query the AutoPush DC schema instance.
    *   **Source Blocked Automated Downloads:** BLS upgraded their security posture using TLS Fingerprinting, which blocked automated python scripts with a `403 Forbidden` error. Resolved by using the `curl_cffi` library to mimic a standard browser's TLS handshake signature.
