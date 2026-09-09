# Rule 18: Single-DCID Node Declarations and MCF Comma Prevention

## 1. Rule Description
This rule ensures that every `Node:` declaration in MCF files defines exactly one valid Data Commons Identifier (DCID) and contains **no commas (`,`)**. Additionally, it verifies that any structural hierarchy properties like `specializationOf:` or `memberOf:` are aligned to reference the corrected consolidated parent DCID (using double-underscore `__` joiners) instead of being split by commas.

## 2. Files Involved
*   **Output MCF / Statvars-Group Files:** All MCF files located in the target dataset's `schema` directory (e.g. `SDG_statvars_groups.mcf`, `sdg_stat_vars.mcf`, etc.).

## 3. Validation Logic & Flow
1.  **Iterate MCF Files:** Loop through all `*.mcf` files in the schema and groups directories.
2.  **Verify `Node:` lines:** For every line starting with `Node:`, assert that the character `,` does not exist in the DCID identifier value. Commas indicate multi-DCID nodes which are syntactically invalid and will crash the MCF parser.
    *   *Correct format:* Use `__` to combine multiple identifiers (e.g., `Node: dcid:A__B__C`).
    *   *Incorrect format:* Using `,` (e.g., `Node: dcid:A,dcid:B,dcid:C`).
3.  **Validate `specializationOf:` and `memberOf:` alignments:**
    *   If a node has a parent relation referencing consolidated identifiers, ensure they use `__` joiners to match the actual consolidated parent `Node` DCID.
    *   If left comma-separated (e.g. `specializationOf: dcid:A,dcid:B,dcid:C`), the parser interprets them as three separate references, breaking the inheritance tree if the parent node was corrected to `dcid:A__B__C`.

## 4. Python Implementation Strategy (Draft)

```python
import os
import glob

class Rule18Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 18 (Single-DCID Node Declarations and Comma Prevention)")
        mcf_files = glob.glob(os.path.join(self.schema_dir, "*.mcf"))
        errors = []
        
        for mcf_file in mcf_files:
            with open(mcf_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    clean_line = line.strip()
                    if clean_line.startswith("Node:"):
                        node_val = clean_line.replace("Node:", "").strip()
                        if ',' in node_val:
                            err_msg = f"Malformed Node with commas at line {line_num}: {clean_line}"
                            self.log_error(err_msg)
                            errors.append(err_msg)
        
        return len(errors) == 0
```
