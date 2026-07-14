# Rule 4: Time Period to observationDate

## Objective
Ensure that the `TIME_PERIOD` (or `timePeriod`) column in the source data accurately maps to the Data Commons `observationDate` property in the output CSV, adhering to the new conversion requirements for complex formats.

## File References
- **Input Data File:** Source data file containing the `TIME_PERIOD` column.
- **Output CSV:** Transcoded data file (e.g., `processed_data/*_data.csv`).

## Validation Logic & Flow
1. **Extraction:** Read the `TIME_PERIOD` column from the input source data.
2. **Target Resolution:** Read the corresponding `observationDate` column in the generated output CSV via `#input` linkage.
3. **Verification Checks:** 
   - **Conversion Check:** The data pipeline converts non-standard date formats into standard formats. Check if `observationDate` equals the first 4 characters (YYYY) of the `TIME_PERIOD` string.
   - **Interval Start Date Extraction:** If the input time format is an ISO-8601 interval (e.g., `2014-01/P3M`), the data pipeline accurately extracts the start date component (`2014-01`). Check if `observationDate` equals this start date.
   - **Fallback Check:** If the conversion checks fail, check if `observationDate` exactly matches the full `TIME_PERIOD` string. This ensures that unconvertible formats are passed through unaltered.

## Python Implementation Strategy
```python
import pandas as pd

def validate_time_period(input_csv_path, output_csv_path):
    # Load data
    input_df = pd.read_csv(input_csv_path)
    output_df = pd.read_csv(output_csv_path)
    
    target_col = 'observationDate'
    source_col = 'timePeriod'
    
    if target_col not in output_df.columns:
        print(f"ERROR: Target column '{target_col}' not found in output CSV.")
        return False
        
    if source_col not in input_df.columns:
        source_cols_upper = {c.upper(): c for c in input_df.columns}
        if 'TIME_PERIOD' in source_cols_upper:
            source_col = source_cols_upper['TIME_PERIOD']
        else:
            print(f"ERROR: Source column representing Time Period not found in input CSV.")
            return False

    success = True
    for idx, row in output_df.iterrows():
        # Get input row via #input logic
        # For simplicity in this pseudocode, assuming 1:1 same row index
        input_time = str(input_df.loc[idx, source_col]).strip()
        actual_obs_date = str(row[target_col]).strip()
        
        # 1. YYYY format check
        yyyy_format = input_time[:4]
        
        if actual_obs_date == yyyy_format:
            continue
            
        # 2. Straight string equivalence check
        if actual_obs_date == input_time:
            continue
            
        # 3. Interval start date check
        if '/' in input_time:
            start_date = input_time.split('/')[0]
            if actual_obs_date == start_date:
                continue
            
        print(f"FAILED: Time Period mismatch. Expected '{yyyy_format}', '{start_date}', or '{input_time}', Found: '{actual_obs_date}'")
        success = False
            
    return success
```

## Example Scenario
- **Input `timePeriod`:** `2015`
- **Output CSV Column (`observationDate`):** `2015`
- **Validation Result:** Pass

- **Input `timePeriod`:** `2024-25/P3M`
- **Output CSV Column (`observationDate`):** `2024-25`
- **Validation Result:** Pass (successfully extracted interval start date).

- **Input `timePeriod`:** `ComplexData`
- **Output CSV Column (`observationDate`):** `ComplexData`
- **Validation Result:** Pass (fallback to string equivalence).
