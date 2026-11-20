# Rule 7: UNIT_MULTIPLIER Application

## Mapping Logic
1. **Identify Multiplier Attribute:** Identify the column representing the unit multiplier in the raw input data (often named `UNIT_MULT`, `UNIT_MULTIPLIER`, etc., depending on the DSD).
2. **Lookup Factor:** Use the common PV map `all_data/pvmap/CL_MULT_pvmap_multiply.csv` to resolve the multiplication factor. The PV map links the multiplier code to a float value (e.g., `1.00E-15` for -15).
3. **Apply Factor:** The expected value in the Data Commons output CSV should be:
   `Expected_Value = float(Raw_OBS_VALUE) * float(Multiplier_Factor)`
4. **Compare:** Assert that `Expected_Value` matches the `value` column in the processed output CSV.

## Relevant Files
- **Raw Input Data:** Varies per dataset (e.g., `SDG_q1-2026_OBS_AG_FOOD_WST_data.csv`).
- **PV Map for Multipliers:** `all_data/pvmap/CL_MULT_pvmap_multiply.csv`.
- **Processed Output Data:** Varies per dataset (e.g., `SDG_q1-2026_OBS_AG_FOOD_WST_data.csv` in `processed_data/`).

## Python Implementation Strategy

```python
import pandas as pd
import numpy as np

def validate_unit_multiplier(input_csv_path: str, output_csv_path: str, dsd_path: str, pvmap_path: str = "all_data/pvmap/CL_MULT_pvmap_multiply.csv"):
    """
    Validates that the UNIT_MULTIPLIER factor is applied to the output values.
    """
    # 1. Load the PV map for multipliers
    # Format: UnCodeKey,prop,val -> e.g., UNIT_MULT:-15,#Multiply,1.00E-15
    multiplier_map = {}
    pv_df = pd.read_csv(pvmap_path)
    for _, row in pv_df.iterrows():
        key = str(row['UnCodeKey']) # e.g., 'UNIT_MULT:-15'
        val = float(row['val'])     # e.g., 1e-15
        multiplier_map[key] = val

    # 2. Identify the multiplier column from DSD
    dsd_df = pd.read_csv(dsd_path)
    
    # Check if there is a multiplier attribute
    multiplier_cols = dsd_df[dsd_df['COLUMN_NAME'].str.upper().str.contains('MULT|MULTIPLIER')]['COLUMN_NAME'].tolist()
    
    if not multiplier_cols:
        return [] # No multiplier column in this dataset
        
    mult_col = multiplier_cols[0]
    
    # 3. Read input and output data
    input_df = pd.read_csv(input_csv_path)
    output_df = pd.read_csv(output_csv_path)
    
    # Ensure order aligns for row-by-row comparison, or merge on keys
    # Assuming direct row equivalence for simplicity, but ideally merge on dimensions
    if len(input_df) != len(output_df):
        return ["Row count mismatch between input and output CSV."]
    
    validation_errors = []
    
    # 4. Validate multiplication
    for idx, (in_row, out_row) in enumerate(zip(input_df.iterrows(), output_df.iterrows())):
        _, input_data = in_row
        _, output_data = out_row
        
        if pd.isna(input_data[mult_col]):
            continue # No multiplier for this row
            
        mult_val = str(input_data[mult_col])
        # Construct the key expected in the PV Map
        # Note: Depending on data, this might just be mult_col + ":" + mult_val
        pv_key = f"{mult_col.upper()}:{mult_val}"
        
        if pv_key in multiplier_map:
            factor = multiplier_map[pv_key]
            
            raw_val = float(input_data['OBS_VALUE']) if 'OBS_VALUE' in input_data else float(input_data.get('value', 0))
            expected_val = raw_val * factor
            
            actual_val = float(output_data['value'])
            
            # Allow minor floating point drift
            if not np.isclose(expected_val, actual_val, rtol=1e-5):
                validation_errors.append(f"Row {idx}: Multiplier validation failed. Raw: {raw_val}, Factor: {factor}, Expected: {expected_val}, Actual: {actual_val}")
        else:
            validation_errors.append(f"Row {idx}: Multiplier key '{pv_key}' not found in PV map.")
            
    return validation_errors
```