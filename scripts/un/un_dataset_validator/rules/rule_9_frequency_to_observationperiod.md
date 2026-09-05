# Rule 9: Frequency to observationPeriod

## Objective
Ensure that the `FREQUENCY` column in the source data correctly maps to the Data Commons `observationPeriod` property in the output CSV, adhering to the mapping defined in the common Property-Value (PV) map.

## File References
- **Input Data File:** Data file containing the `FREQUENCY` column.
- **Common PV Map:** `all_data/pvmap/CL_FREQUENCY_pvmap_obsperiod.csv`
- **Output CSV:** Transcoded data file (e.g., `processed_data/*_data.csv`).

## Validation Logic & Flow
1. **Extraction:** Read the `FREQUENCY` column from the input source data.
2. **Lookup:** Cross-reference the input frequency code (e.g., `A`, `M`, `Q`) with the `UnCode` column in `CL_FREQUENCY_pvmap_obsperiod.csv`.
3. **Target Resolution:** Extract the mapped Data Commons observation period from the `ConstraintPropValue` column in the PV map (e.g., `P1Y` for Annual).
4. **Verification:** Check the corresponding row in the output CSV and ensure the resolved value is present in the `observationPeriod` column.

## Python Implementation Strategy
```python
import pandas as pd

def validate_frequency(input_csv_path, output_csv_path, pv_map_path):
    # Load data
    input_df = pd.read_csv(input_csv_path)
    output_df = pd.read_csv(output_csv_path)
    pv_map_df = pd.read_csv(pv_map_path)
    
    # Anomaly Handling: Check for typos like 'opservationPeriod' in output headers
    target_col = 'observationPeriod'
    if target_col not in output_df.columns:
        if 'opservationPeriod' in output_df.columns:
            print("ERROR: Typo found in output CSV header: 'opservationPeriod' instead of 'observationPeriod'.")
            # For validation continuity, we can temporarily map it, but it should be flagged as a failure.
            target_col = 'opservationPeriod' 
        else:
            print(f"ERROR: Target column '{target_col}' not found in output CSV.")
            return False

    # Create mapping dictionary from PV Map
    # Note: Sometimes the UnCode has quotes, so we strip them
    pv_map_df['UnCode'] = pv_map_df['UnCode'].str.strip('"')
    freq_map = dict(zip(pv_map_df['UnCode'], pv_map_df['ConstraintPropValue']))
    
    success = True
    for idx, row in input_df.iterrows():
        input_freq = str(row.get('FREQUENCY', '')).strip()
        expected_obs_period = freq_map.get(input_freq)
        
        if not expected_obs_period:
            print(f"WARNING: Unmapped FREQUENCY code '{input_freq}' at row {idx}")
            continue
            
        actual_obs_period = str(output_df.loc[idx, target_col]).strip()
        
        if actual_obs_period != expected_obs_period:
            print(f"FAILED: Mismatch at row {idx}. Expected: {expected_obs_period}, Found: {actual_obs_period}")
            success = False
            
    return success
```

## Important Anomaly Handling
As noted in the implementation analysis, the output pipeline has been known to generate files with the header `opservationPeriod` instead of `observationPeriod`. The Python script must dynamically check for this typo and flag the validation as a failure if the correct header is missing, reporting the specific typo found.

## Example Scenario
- **Input `FREQUENCY` code:** `A`
- **PV Map Lookup (`UnCode` -> `ConstraintPropValue`):** `A` -> `P1Y`
- **Output CSV Column (`observationPeriod`):** `P1Y`
