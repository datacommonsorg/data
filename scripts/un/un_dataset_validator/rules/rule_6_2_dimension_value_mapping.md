# Rule 6.2: Dimension Value Mapping

## Objective
Ensure that every value within a dimension column is properly mapped to a generated property value DCID following the exact template: `<prefix>_<CONCEPT>-<CODE>`.

## Context & Rationale
According to the meeting notes and project requirements, any column designated as a "dimension" in the Dataset Definition (DSD) file must have its distinct values transformed into standardized Data Commons Identifiers (DCIDs). The format for these DCIDs consistently incorporates a prefix (typically `UN`), the concept name (derived from the column name), and the specific value code. 

For instance, if the dimension column is `product` and a raw value in the dataset is `CPC2_1_0113`, the mapped value DCID should be formatted as `UN_PRODUCT-CPC2_1_0113`. In the output schema/MCF, this would appear as a property-value pair like `product: dcid:UN_PRODUCT-CPC2_1_0113`.

## Files Involved
*   **DSD File (e.g., `schema.csv` or `DSD.csv`):** Used to identify which columns act as dimensions (where `ROLE` = `Dimension`).
*   **Input Data File (`.csv`):** Provides the raw source values for the identified dimension columns.
*   **Output Files (`.mcf`, `.tmcf`, or processed `.csv`):** Validated to ensure the final output respects the mapped DCID format.

## Verification Logic
1.  **Identify Dimensions:** Read the DSD file and filter for rows where the `ROLE` column is explicitly set to `Dimension` (excluding explicit exceptions like Geography, Time Period, OBS_VALUE, and Series, which have their own rules).
2.  **Extract Concept Names:** Determine the concept name from the dimension's column name. The concept name is generally the uppercase version of the column name (e.g., `product` -> `PRODUCT`).
3.  **Construct Expected DCIDs:** For every row in the input data file, look at the value under the dimension column. Construct the expected DCID using the template:
    *   `Prefix`: `UN` (or derived from the specific dataset configuration).
    *   `Concept`: Capitalized column name.
    *   `Code`: The raw value found in the input data.
    *   **Format:** `<prefix>_<CONCEPT>-<CODE>` (e.g., `UN_PRODUCT-CPC2_1_0113`).
4.  **Validate Output:** Ensure that in the finalized statistical variable mapping or output nodes, the dimension property maps exactly to this constructed DCID (e.g., checking that `product: dcid:UN_PRODUCT-CPC2_1_0113` exists).

## Python Implementation Strategy

```python
import pandas as pd
import re

def validate_dimension_value_mapping(dsd_path: str, data_csv_path: str, output_mcf_path: str, prefix: str = "UN"):
    """
    Validates that values for dimension columns are mapped to the correct DCID template.
    """
    # 1. Read DSD and identify dimension columns
    dsd_df = pd.read_csv(dsd_path)
    
    # Identify dimensions but exclude Geography, Time Period, OBS_VALUE, and SERIES as per rules
    exclusions = ['GEOGRAPHY', 'TIME PERIOD', 'OBS_VALUE', 'TIME_PERIOD', 'SERIES']
    dimensions = dsd_df[
        (dsd_df['ROLE'].str.upper() == 'DIMENSION') & 
        (~dsd_df['COLUMN_NAME'].str.upper().isin(exclusions))
    ]['COLUMN_NAME'].tolist()
    
    # 2. Read input data to collect unique values for each dimension
    data_df = pd.read_csv(data_csv_path)
    
    expected_mappings = {}
    for dim in dimensions:
        if dim in data_df.columns:
            concept = dim.upper()
            unique_values = data_df[dim].dropna().unique()
            expected_dcids = []
            for val in unique_values:
                # Convert special characters to underscores (as per notes)
                clean_val = re.sub(r'[^a-zA-Z0-9_]', '_', str(val))
                expected_dcids.append(f"{prefix}_{concept}-{clean_val}")
                
            expected_mappings[dim] = expected_dcids
            
    # 3. Read output MCF/TMCF file content to verify
    with open(output_mcf_path, 'r') as f:
        mcf_content = f.read()
        
    validation_errors = []
    
    # 4. Verify that the constructed DCIDs exist in the output mapping
    for dim, expected_dcids in expected_mappings.items():
        for expected_dcid in expected_dcids:
            # Check for property: dcid:<Expected_DCID> format
            # e.g., product: dcid:UN_PRODUCT-CPC2_1_0113
            # NOTE: Series is a dimension but maps to populationType, which may need a custom check.
            expected_string = f"{dim}: dcid:{expected_dcid}"
            
            if expected_string not in mcf_content:
                # Also fallback to check just the DCID presence in case property name differs
                if expected_dcid not in mcf_content:
                    validation_errors.append(
                        f"Missing or incorrectly formatted dimension mapping. "
                        f"Expected to find: {expected_dcid} for dimension '{dim}'."
                    )
                    
    return validation_errors

# Example usage:
# errors = validate_dimension_value_mapping('schema.csv', 'data.csv', 'output.mcf')
# if errors:
#     for e in errors:
#         print(e)
```

## Edge Cases to Consider
*   **Special Characters:** If the raw value (`<CODE>`) contains special characters or spaces, they must be converted to underscores before constructing the DCID (as per the separate special character conversion rule).
*   **Case Sensitivity:** Ensure that the prefix and concept are properly cased (e.g., uppercase `UN` and `PRODUCT`) while the value code's case might depend on specific entity resolution rules (typically preserved or uppercase).
*   **Missing Values:** If a dimension column has a missing/null value for a specific row, the validation script should safely ignore it or flag it as an error based on strictness requirements, rather than generating an invalid DCID like `UN_PRODUCT-nan`.
