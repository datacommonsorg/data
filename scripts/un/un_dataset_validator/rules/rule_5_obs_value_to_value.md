# Rule 5: OBS_VALUE Mapping to `value`

## 1. Rule Description
* **Core Rule (5):** The observation value (`OBS_VALUE` column) from the input data must be mapped to the `value` property in the output CSV.
* **Format Check:** As per the meeting notes, observation values are required to map to `value.number`. This means the resulting `value` must be a valid number (`{Number}`). This validation check must be performed using the property-value (PV) map.

## 2. Files Involved
* **Input Dataset:** The raw input `.csv` data files containing the `OBS_VALUE` column.
* **Output Data File:** The generated output `.csv` file.
* **Property Value Map (PV Map):** Specifically, the `common_pvmap_obs.csv` file which defines the mapping rule: `OBS_VALUE,value,{Number},...`

## 3. Concrete Example
* **Input Data Row:** Contains an `OBS_VALUE` of `594982.4482`.
* **Output Check:** The output `.csv` file should contain a column named `value`, and the corresponding row must contain `594982.4482` (or potentially a multiplied value if unit multipliers apply, see Rule 10, but inherently it must be numeric).

## 4. Validation Logic & Flow
1. **Identify the Input and Output Files:** Pair the input dataset `.csv` file with its corresponding generated output `.csv` file.
2. **Column Verification:**
   * Verify that the input file has an `OBS_VALUE` column.
   * Verify that the output file has a `value` column.
3. **Row-by-Row Mapping Validation:**
   * For each row in the input, locate the matching row in the output (this may require a row identifier like `#input`).
   * **Value Mapping Check:** The `OBS_VALUE` should be correctly transferred to the `value` column.
   * **Number Validation:** Ensure that the data in the output `value` column can be parsed as a float/number.

## 5. Python Implementation Strategy

```python
import pandas as pd

def validate_rule_5(input_csv_path: str, output_csv_path: str) -> dict:
    """
    Validates Rule 5: OBS_VALUE maps to value and is numeric.
    """
    errors = []
    
    try:
        input_df = pd.read_csv(input_csv_path)
        output_df = pd.read_csv(output_csv_path)
    except Exception as e:
        return {"status": "FAILED", "errors": [f"File read error: {e}"]}

    if 'OBS_VALUE' not in input_df.columns:
        # Assuming all valid input files must have OBS_VALUE for this rule to apply
        return {"status": "SKIPPED", "message": "No OBS_VALUE column in input."}
        
    if 'value' not in output_df.columns:
        errors.append("Output CSV is missing the 'value' column.")
        return {"status": "FAILED", "errors": errors}

    # Verify that all entries in the output 'value' column are numeric
    # We use pd.to_numeric with errors='coerce' which turns non-numeric into NaN
    numeric_values = pd.to_numeric(output_df['value'], errors='coerce')
    
    # Check for rows where the value became NaN (but wasn't originally empty)
    non_numeric_mask = numeric_values.isna() & output_df['value'].notna()
    
    if non_numeric_mask.any():
        bad_rows = output_df[non_numeric_mask].index.tolist()
        errors.append(f"Found non-numeric values in the 'value' column at output row indices: {bad_rows[:5]}...")

    if errors:
        return {"status": "FAILED", "errors": errors}
    return {"status": "PASSED"}
```

## 6. Edge Cases & Considerations
* **Empty/Missing Values:** How should missing or empty `OBS_VALUE` entries be handled? They should likely map to empty/missing in the output `value` and not fail the numeric check.
* **Multipliers (Rule 10 Interaction):** If a unit multiplier is present, the final `value` in the output will be `OBS_VALUE * MULTIPLIER`. The validation script might need to account for this multiplication rather than expecting an exact string match. However, the requirement that the resulting `value` is `{Number}` remains absolute.
* **Special Characters:** Check for formatted numbers in the input (e.g., `"1,000.50"`). These must be clean numeric values (e.g., `1000.50`) in the output.
