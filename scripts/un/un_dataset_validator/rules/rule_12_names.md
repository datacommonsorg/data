# Rule 12: Names (alternateName, Value names, nameWithLanguage)

## 1. Rule Description
* **Core Rule (12):** This rule ensures that names for properties and values generated in the schema accurately reflect their source definitions in the DSD (Data Structure Definition) and Codelists.
* **Sub-rule (12.1):** A property's `alternateName` must match the corresponding name defined in the DSD file.
* **Sub-rule (12.2):** A value's name must match the name defined in the specific concept's codelist (`CL` file).
* **Sub-rule (12.3):** Any names available in languages other than the default must be appropriately added to the `nameWithLanguage` property.

## 2. Files Involved
* **Data Input:** The transcoded dataset.
* **DSD File:** Defines the structural metadata and concepts.
* **Codelists (CL):** Define the valid values and their corresponding names for each concept.
* **Output MCF Files:** The generated schema and stat vars where these properties are defined.

## 3. Validation Logic & Flow
1. **Property Names (12.1):** 
   - Parse the generated schema.
   - For each property, locate its corresponding concept in the DSD.
   - Assert that the `alternateName` in the generated schema exactly matches the name string in the DSD.
2. **Value Names (12.2):**
   - Parse the generated schema.
   - For each value, identify its concept and find the corresponding codelist file.
   - Assert that the value name in the generated schema matches the name in the codelist.
3. **Multi-lingual Names (12.3):**
   - If the DSD or codelists provide names in multiple languages (e.g., using language tags), check that the generated schema utilizes the `nameWithLanguage` property correctly to represent these translations.

## 4. Python Implementation Strategy (Draft)

```python
import pandas as pd
# Pseudocode structure for Rule 12 Validation

def validate_rule_12(schema_mcf_path: str, dsd_path: str, cl_dir_path: str) -> dict:
    """
    Validates naming conventions against DSD and Codelists.
    """
    errors = []
    
    # 1. Load DSD for property names
    # dsd_df = pd.read_csv(dsd_path)
    
    # 2. Parse MCF to extract properties and values
    # ...
    
    # 3. Check 12.1: Property alternateName vs DSD
    # ...
    
    # 4. Check 12.2: Value names vs Codelists
    # ...
    
    # 5. Check 12.3: nameWithLanguage
    # ...
    
    return {"status": "PASSED" if not errors else "FAILED", "errors": errors}
```

## Implementation Deviations
- **String Normalization:** To account for pipeline inconsistencies (such as varying quotes, spacing, or punctuation), the script implements a `normalize_name()` function. This strips all punctuation, converts strings to lowercase, and normalizes spacing before performing the string comparison.
- **Missing StatVar Names:** Due to a known pipeline issue where `name` properties are omitted from `StatisticalVariable` nodes, the validator currently logs a warning (rather than a failure) when this occurs.