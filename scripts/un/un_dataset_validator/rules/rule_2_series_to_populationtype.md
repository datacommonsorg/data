# Rule 2: SERIES Mapping to `populationType`

## 1. Rule Description
* **Core Rule (2):** The `series` identifier from the input file must be mapped to the `populationType` property on the generated Statistical Variable nodes in the output `.mcf` file.
* **Sub-rule (2.1):** The series code in the `populationType` must be prefixed with the responsible agency's identifier in the format: `UN_<AGENCY_NAME>_SERIES-<SERIES_CODE>`.

## 2. Files Involved
* **Input Dataset / Context:** The raw input data containing the series information. The series code can typically be derived from the input filename (e.g., `SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv` implies the series `AG_FLS_INDEX`) or from an explicit column within the input CSV.
* **Output MCF File:** The generated StatVars file (e.g., `SDG_q1-2026_OBS_AG_FLS_INDEX_data_stat_vars.mcf`).

## 3. Concrete Example (SDG Dataset)
* **Dataset Context:** `SDG` (derived from the folder name `sdg_q1-2026`). Agency becomes `SDG`.
* **Input Series:** `AG_FLS_INDEX`.
* **Expected Prefix Formation:** `UN_` + `SDG` + `_SERIES-` + `AG_FLS_INDEX` = `UN_SDG_SERIES-AG_FLS_INDEX`.
* **Output Check:** Look at the `.mcf` file. For a node like `Node: dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_ANIMAL_PROD`, you must find the exact property line:
  ```
  populationType: dcid:UN_SDG_SERIES-AG_FLS_INDEX
  ```

## 4. Validation Logic & Flow
1. **Determine the Agency Context:** The script should determine the agency (e.g., `SDG`, `ILO`, `UNICEF`) based on the root directory of the dataset being processed (e.g., `/all_data/sdg_q1-2026` -> agency is `SDG`).
2. **Determine the Series Code:** Extract the expected series code for the current file being validated.
3. **Parse the Output MCF:** Read the `output_stat_vars.mcf` file. Group properties by their `Node: dcid:...` definition block.
4. **Validate Nodes:** Iterate through all parsed nodes where `typeOf: dcid:StatisticalVariable`. 
   * Check if the `populationType` key exists.
   * Assert that its value exactly equals `dcid:UN_<AGENCY>_SERIES-<SERIES_CODE>`.

## 5. Python Implementation Strategy

```python
import os

def validate_rule_2(mcf_filepath: str, expected_series_code: str, agency_name: str) -> dict:
    """
    Validates Rule 2 & 2.1: SERIES mapped to populationType with agency prefix.
    """
    agency_upper = agency_name.upper()
    expected_population_type = f"dcid:UN_{agency_upper}_SERIES-{expected_series_code}"
    
    # Assuming a helper function parse_mcf(filepath) returns a list of dictionaries 
    # where each dictionary represents a Node and its properties.
    mcf_nodes = parse_mcf(mcf_filepath) 
    
    errors = []
    
    for node in mcf_nodes:
        if node.get('typeOf') == 'dcid:StatisticalVariable':
            node_id = node.get('Node')
            actual_population_type = node.get('populationType')
            
            if not actual_population_type:
                errors.append(f"Node {node_id} is missing 'populationType'.")
            elif actual_population_type != expected_population_type:
                errors.append(f"Node {node_id} has incorrect populationType. "
                              f"Expected '{expected_population_type}', got '{actual_population_type}'.")
                
    if errors:
        return {"status": "FAILED", "errors": errors}
    return {"status": "PASSED"}

# Example Usage:
# validate_rule_2(".../SDG_q1-2026_OBS_AG_FLS_INDEX_data_stat_vars.mcf", "AG_FLS_INDEX", "SDG")
```

## 6. Edge Cases & Considerations
* **Missing `populationType`:** If the `populationType` is completely absent from a StatVar node, the validation should fail for that specific node.
* **Case Sensitivity:** Ensure the agency name is converted to uppercase (e.g., `sdg` -> `SDG`) before forming the expected DCID string.
* **Non-StatVar Nodes:** Ensure the validation only runs on nodes where `typeOf: dcid:StatisticalVariable`. Other nodes defined in the MCF (if any) should not trigger false positives.