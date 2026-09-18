# Rule 10: Attributes as Output Columns

## Description
According to the UN Data Commons mapping rules, every concept defined in the dataset's Data Structure Definition (DSD) file with a `ROLE` of `Attribute` must be present as a separate column in the output `data.csv` file. 

Attributes provide supplementary information (such as footnotes, observation statuses, or flags) about the observation value. Unlike dimensions, attributes must **NOT** be attached as properties to the Statistical Variables.

**Note on Exclusions (Rule 10.1):** Parsing and validating the internal string structures of complex attributes (e.g., verifying comma-separated multiple footnotes inside a single `FOOTNOTE` cell) is marked as an "Ask Ajai" item and is strictly excluded from this validation check. This rule only validates the *presence* of the attribute column in the output.

## Files Involved
- **Input:** Dataset-specific DSD file (e.g., `schema/dsd.csv` or similar file defining `ROLE`).
- **Output:** The generated data CSV file (e.g., `SDG_q1-2026_OBS_AG_FOOD_WST_data.csv`).

## Validation Logic
1. **Identify Attributes:** Parse the DSD file and filter for all rows where the `ROLE` column is equal to `Attribute` (case-insensitive).
2. **Extract Identifiers:** Extract the concept identifier/name for each attribute (e.g., `OBS_STATUS`, `FOOTNOTE`).
3. **Verify Output Columns:** Read the header of the generated output `data.csv` file.
4. **Compare:** Ensure that every attribute identified in step 1 exists as a distinct column in the output CSV header.
5. **Report Missing Columns:** If an attribute defined in the DSD is missing from the output CSV, flag it as a validation failure.

## Python Implementation

```python
import pandas as pd
import glob
import os

def validate_rule_10(dsd_file_path: str, output_csv_path: str) -> bool:
    """
    Validates that all concepts with ROLE='Attribute' in the DSD are present as 
    columns in the output CSV.
    """
    print(f"Validating Rule 10: Attributes as Output Columns for {os.path.basename(output_csv_path)}")
    
    try:
        # 1. Read DSD and find Attributes
        dsd_df = pd.read_csv(dsd_file_path)
        
        # Ensure required columns exist
        # Note: Actual column names for Concept/Identifier and Role might vary slightly
        # Adjust 'concept' and 'role' based on the exact DSD schema structure.
        role_col = next((c for c in dsd_df.columns if c.strip().lower() == 'role'), None)
        concept_col = next((c for c in dsd_df.columns if c.strip().lower() in ['concept', 'id', 'name']), None)
        
        if not role_col or not concept_col:
            print(f"  [ERROR] DSD file missing 'ROLE' or Concept identifier column.")
            return False
            
        # Filter attributes and get their names
        attributes = dsd_df[dsd_df[role_col].str.lower() == 'attribute'][concept_col].dropna().tolist()
        # Clean up strings
        expected_attribute_cols = [attr.strip() for attr in attributes]
        
        if not expected_attribute_cols:
            print("  [INFO] No attributes found in DSD. Validation passed.")
            return True
            
        # 2. Read Output CSV headers
        output_df = pd.read_csv(output_csv_path, nrows=0) # Read only header
        output_columns = [col.strip() for col in output_df.columns]
        
        # 3. Verify presence
        missing_attributes = []
        for attr in expected_attribute_cols:
            # Check exact match or case-insensitive match based on pipeline behavior
            match_found = any(attr.lower() == col.lower() for col in output_columns)
            if not match_found:
                missing_attributes.append(attr)
                
        if missing_attributes:
            print(f"  [FAILURE] Missing Attribute columns in output CSV: {missing_attributes}")
            return False
            
        print("  [SUCCESS] All DSD Attributes are present as columns in the output CSV.")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Validation failed due to exception: {e}")
        return False

# Example Usage:
# validate_rule_10('schema/dsd.csv', 'extracted_data_new/20260615/SDG_q1-2026_OBS_AG_FOOD_WST_data.csv')
```
