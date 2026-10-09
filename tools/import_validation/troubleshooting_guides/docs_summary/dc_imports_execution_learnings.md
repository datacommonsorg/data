# Google Sheet: DC - Imports Execution Learnings Summary

*   **Original URL:** https://docs.google.com/spreadsheets/d/1lAm-EPB6o9U9btQHbdRruGhx_DFerlhQF43Ba6skI4Q/edit
*   **Purpose/Overview:** This spreadsheet tracks ongoing execution learnings, issues, and recommendations across multiple Data Commons import pipelines.
*   **Key Entries & Actions:**
    *   **Unexpected Characters:** Source data issues resolved by implementing PV Mapping and processor code changes.
    *   **Missing Places/DCIDs:** Validation failures resolved by manually adding missing places to production (e.g. `b/472258775`).
    *   **Pipeline Automation:** Recommendation to convert Semi-Auto Refresh setups into Full Auto Refresh pipelines to minimize manual restarts (e.g. `b/474348464`).
    *   **Hangs and Performance:** Documented cases of copy service hangs requiring manual restarts, and low parallel performance in the KG Import UI.
