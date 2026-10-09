# Rule 17: Name Constraints (Bracket and Code Prohibitions)

## 1. Rule Description
This rule ensures that the generated `name` properties in the dataset's schemas are properly formatted, human-readable, and descriptive. It combines two core checks targeting the `name` property:
*   **Bracket Check (17.1):** A node's `name` must not start with a bracket `[` (ignoring leading whitespace). This ensures that names are not just templates or missing descriptions.
*   **Code Concept Check (17.2):** A node's `name` must not contain technical identifier codes, concept codes, or file/side identifiers (such as `CL_`, `DSD_`, `FSP`, `TFT`, or uppercase value codes like `ISCED11_02`).

## 2. Files Involved
*   **Output MCF Files:** All MCF files located in the target dataset's `schema` directory (e.g. `sdg_q1-2026_stat_vars.mcf`, `un_codelist_schema_*.mcf`, etc.).

## 3. Validation Logic & Flow
1.  **Iterate Schema Files:** Loop dynamically through all `*.mcf` files in the target dataset's `schema/` directory.
2.  **Parse Nodes:** Monitor node IDs and types (`typeOf`).
    *   *Exclusion:* If the node is of type `StatVarGroup` (e.g. `dcs:StatVarGroup`), skip name checks since grouping hierarchy titles naturally contain valid taxonomic labels like `(ISIC4 - A)`.
3.  **Validate `name` Properties:**
    *   *Check 17.1 (Bracket Start):* Extract the raw name value (removing potential enclosing quotes). If the first non-whitespace character is `[`, fail the check.
    *   *Check 17.2 (Technical Codes):* Tokenize the name string. Check if any token matches:
        *   Explicitly forbidden file-side codes like `FSP`, `TFT`, `DSD`, or `CL`.
        *   Uppercase technical prefix/identifier formats (e.g., words starting with `CL_` or `DSD_`).
        *   Uppercase value codes containing underscores (such as `ISCED11_02`, `AGG_ANIMAL_PROD`, etc.).
    *   *Protect Descriptive Acronyms:* Ensure that common uppercase descriptive words/abbreviations (e.g., `GDP`, `FDI`, `UNCLOS`, `CO2`, `ISIC4`, `MGCI`) do not trigger false positives.

## 4. Python Implementation Strategy (Draft)

```python
import os
import glob
import re

class Rule17Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 17 (Name Constraints)")
        schema_files = glob.glob(os.path.join(self.schema_dir, "*.mcf"))
        prohibited_codes = {"FSP", "TFT", "DSD", "CL"}
        errors = []
        
        for schema_file in schema_files:
            # Parse nodes line-by-line ...
            # 1. Track Node and typeOf
            # 2. Extract name value
            # 3. Perform Bracket Check: name_val.startswith('[')
            # 4. Perform Code Check: search for uppercase codes with underscores or in prohibited_codes
            # ...
        
        return len(errors) == 0
```
