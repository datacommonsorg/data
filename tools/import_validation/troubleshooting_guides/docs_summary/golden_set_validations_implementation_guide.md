# Google Doc: Implementation Guide: Golden Set Validations Summary

*   **Original URL:** https://docs.google.com/document/d/14Fpe5e9jSzzJ5_QTcqQ1AFb2oqjJzXuc1_BmQCX-uns/edit
*   **Purpose/Overview:** This is a technical guide designed to help users implement "Golden Set Validations" to protect data imports from regressions and accidental data loss.
*   **Problem Description:** The guide addresses recurring data deletion failures by establishing baselines (golden files) that the system can use to verify new data against expected results.
*   **Root Causes:** General lack of automated baseline comparisons for data integrity.
*   **Resolutions/Findings:** The guide recommends implementing two primary validations: `Check_goldens_output_csv` (for final output data) and `Check_goldens_summary_report` (for structural metrics). It also defines a mandatory directory structure including a `golden_data/` folder and a `validation_config.json` file to manage tolerance thresholds.
