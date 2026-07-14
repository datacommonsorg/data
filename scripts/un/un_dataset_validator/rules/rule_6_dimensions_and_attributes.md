# Rule 6: Dimensions vs. Attributes

## 1. Rule Description
* **Core Rule (6):** All properties defined in the Dataset Definition (DSD) file must be correctly handled as either a **dimension** or an **attribute**. 
* **Dimensions:** Except for specific exemptions (`Geography`, `Time Period`, `OBS_VALUE`, and `SERIES`), any property marked as a "dimension" must be attached to the Statistical Variable (StatVar) as a **constraint property**.
* **Attributes:** Any property marked as an "attribute" must **not** be attached to the Statistical Variable. Instead, it must be included in the output data `.csv` as a separate column.

## 2. Files Involved
* **Input DSD File:** The respective DSD file for the dataset (e.g., an Excel/CSV file containing the `ROLE` column with values "dimension" or "attribute").
* **Input Data File:** The raw `.csv` data.
* **Output Data File:** The generated output `.csv` file.
* **Output MCF File:** The generated `.mcf` file containing the Statistical Variable definitions.

## 3. Concrete Example
* **DSD Definition:** 
  * `PRODUCT` is defined with a `ROLE` of "dimension".
  * `CENSORED_VALUE_TYPE` is defined with a `ROLE` of "attribute".
* **Output Check for Dimension (`PRODUCT`):** 
  * The Statistical Variable node (e.g., `Node: dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_CRL_PUL`) in the `.mcf` file must contain `PRODUCT` as a constraint property (e.g., `product: dcid:UN_PRODUCT-AGG_CRL_PUL`).
* **Output Check for Attribute (`CENSORED_VALUE_TYPE`):** 
  * The StatVar node must **not** contain `CENSORED_VALUE_TYPE`.
  * The output `.csv` file must contain a separate column named `censoredValueType` (or similar mapped name), with values like `UN_CENSORED_VALUE_TYPE-_Z`.

## 4. Validation Logic & Flow
1. **Parse DSD File:** Read the DSD file and extract the list of dimensions and attributes from the `ROLE` column.
2. **Filter Dimensions:** From the list of dimensions, exclude the predefined exemptions: Geography (e.g., `REF_AREA`), Time Period (e.g., `TIME_PERIOD`), and Observation Value (`OBS_VALUE`).
3. **Validate Dimensions in MCF:**
   * Iterate through the generated StatVars in the output `.mcf` file.
   * Verify that the remaining dimensions (e.g., `SEX`, `AGE`, `PRODUCT`) exist as constraint properties attached to the respective StatVar nodes.
4. **Validate Attributes in CSV:**
   * Iterate through the list of attributes defined in the DSD.
   * Verify that they do **not** appear in the StatVar nodes.
   * Verify that they **do** appear as distinct columns in the generated output `.csv` file.

## 5. Python Implementation Strategy

```python
import pandas as pd
import re

def validate_rule_6(dsd_csv_path: str, output_csv_path: str, output_mcf_path: str) -> dict:
    """
    Validates Rule 6: Dimensions as constraint properties, Attributes as separate columns.
    """
    errors = []
    
    try:
        dsd_df = pd.read_csv(dsd_csv_path)
        output_df = pd.read_csv(output_csv_path)
        with open(output_mcf_path, 'r') as f:
            mcf_content = f.read()
    except Exception as e:
        return {"status": "FAILED", "errors": [f"File read error: {e}"]}

    if 'ROLE' not in dsd_df.columns or 'concept' not in dsd_df.columns:
        return {"status": "SKIPPED", "message": "DSD file missing 'ROLE' or 'concept' columns."}

    # Identify Dimensions and Attributes (ignoring case variations if any)
    dimensions = dsd_df[dsd_df['ROLE'].str.lower() == 'dimension']['concept'].tolist()
    attributes = dsd_df[dsd_df['ROLE'].str.lower() == 'attribute']['concept'].tolist()

    # Exemptions
    exemptions = ['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE', 'SERIES']
    target_dimensions = [dim for dim in dimensions if dim.upper() not in [e.upper() for e in exemptions]]

    # Validate Attributes in CSV
    # Attribute names might be mapped (e.g., CENSORED_VALUE_TYPE -> censoredValueType)
    # This check might need fuzzy matching or a mapping dictionary if names differ.
    for attr in attributes:
        # Simplistic check: assumes attribute name in DSD maps to a column name or a variation
        # In practice, you might need a PV map to resolve the exact CSV column name.
        match_found = any(attr.lower() in col.lower().replace("_", "") for col in output_df.columns)
        if not match_found:
             errors.append(f"Attribute '{attr}' not found as a column in the output CSV.")
             
        # Also ensure it is NOT in the MCF as a property
        if re.search(rf'^{attr.lower()}:', mcf_content, re.IGNORECASE | re.MULTILINE):
            errors.append(f"Attribute '{attr}' incorrectly attached to a StatVar in the MCF file.")

    # Validate Dimensions in MCF
    for dim in target_dimensions:
        # Check if the dimension appears as a constraint property in the MCF
        if not re.search(rf'^{dim.lower()}:', mcf_content, re.IGNORECASE | re.MULTILINE):
            # Note: This is a file-level check. A strict row-by-row mapping might be required
            # if only specific StatVars should have specific dimensions.
            errors.append(f"Dimension '{dim}' not found as a constraint property in the MCF file.")
            
    if errors:
        return {"status": "FAILED", "errors": errors}
    return {"status": "PASSED"}
```

## 6. Edge Cases & Considerations
* **Exemptions List:** The list of dimensions to exempt (`Geography`, `Time Period`, and `OBS_VALUE`) might use different column names in different datasets (e.g., `REF_AREA` vs `geography`). The validation script must map these correctly based on the dataset.
* **Naming Conventions:** DSD concept names (e.g., `CENSORED_VALUE_TYPE`) might be camelCased or otherwise transformed when they become output CSV column names (e.g., `censoredValueType`). The validation logic needs to account for this transformation.
* **Missing DSD Columns:** If a DSD file is missing the `ROLE` column, the script needs a fallback or should flag it as an immediate error, as the distinction cannot be made.
