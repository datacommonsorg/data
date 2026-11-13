# Rule 16: Observation Completeness (#input tracking)

## Description
This rule guarantees that no non-empty observations are improperly dropped during processing. The generated `#input` column tracks the origin of each data point, providing a lineage from the source file. Every valid observation cell in the source data should have a corresponding `#input` reference in the output.

## Implementation Details
* **Script:** `scripts/test_rule_16.py`
* **Target:** 
  1. The output `*_data.csv` files generated in the `processed_data` directory.
  2. The raw input `.csv` files stored in the designated input directory.
* **Validation Logic:** 
    1. Parse and extract all `#input` lineage cell references (format `filename:row:col`) from all generated output files.
    2. Scan every raw input file to identify cells containing non-empty observation values (e.g., in `OBS_VALUE` columns).
    3. Ensure that every identified valid input cell maps directly to an extracted `#input` coordinate. 

## Remediation
If this rule fails, it indicates a technical problem with the data pipeline where non-empty points are being unexpectedly omitted. Review the transformation and mapping logic to ensure all valid rows are preserved in the final output.