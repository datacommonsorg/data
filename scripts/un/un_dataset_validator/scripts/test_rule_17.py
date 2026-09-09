"""
VALIDATION RULE:
================
# Rule 17: Name Constraints (Bracket and Code Prohibitions)

## 1. Rule Description
* **Bracket Check:** A `name` property must not start with a bracket character `[` (ignoring leading whitespace).
* **Code Concept Check:** A `name` property must not contain raw concept codes or attribute codes (such as `CL`, `FSP`, `TFT`, or uppercase tokens from the node's own `dcid`). Only descriptive, human-readable names should be present.

## 2. Files Involved
* **Input MCF Files:** All MCF files located in the dataset's `schema` directory.
"""

import os
import sys
import glob
import re

# Add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))
from base_validator import BaseRuleValidator

class Rule17Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 17 (Name Constraints)")
        
        # We dynamically target the schema directory
        schema_pattern = os.path.join(self.schema_dir, "*.mcf")
        schema_files = glob.glob(schema_pattern)
        
        failed = False
        errors = []
        warnings = []
        
        if not schema_files:
            self.write_log(f"No MCF files found in schema directory: {self.schema_dir}")
            failed = True
        else:
            self.write_log(f"Processing {len(schema_files)} MCF files in schema directory...")
            
            # Explicitly prohibited standalone codes
            prohibited_codes = {"FSP", "TFT", "DSD", "CL"}
            
            for schema_file in schema_files:
                filename = os.path.basename(schema_file)
                self.write_log(f"Validating file: {filename}")
                
                current_node_id = None
                current_node_dcid = None
                current_node_type = None
                
                with open(schema_file, 'r', encoding='utf-8') as f:
                    for line_idx, line in enumerate(f, start=1):
                        stripped_line = line.strip()
                        
                        # Track current node ID/dcid
                        if stripped_line.startswith("Node: "):
                            current_node_id = stripped_line[6:].strip()
                            # Extract dcid
                            if current_node_id.startswith("dcid:"):
                                current_node_dcid = current_node_id[5:]
                            else:
                                current_node_dcid = current_node_id
                            current_node_type = None  # Reset type for new node
                            continue
                            
                        if stripped_line.startswith("typeOf: "):
                            current_node_type = stripped_line[8:].strip()
                            continue
                            
                        if stripped_line.startswith("name: "):
                            # Skip StatVarGroup names as they are group titles and naturally contain classification codes
                            if current_node_type and "StatVarGroup" in current_node_type:
                                continue
                                
                            # Extract the raw name string
                            name_val = stripped_line[6:].strip()
                            if name_val.startswith('"') and name_val.endswith('"'):
                                name_val = name_val[1:-1]
                            name_val = name_val.strip()
                            
                            if not name_val:
                                continue
                                
                            # 1. Bracket Check: must not start with '['
                            if name_val.startswith('['):
                                errors.append(
                                    f"{filename}, line {line_idx}: Node '{current_node_dcid}' name starts with a bracket: '{name_val}'"
                                )
                                failed = True
                                
                            # 2. Code Concept Check: must not contain raw concept codes or attribute codes
                            # Tokenize name to check for technical codes (words of letters, digits, underscores)
                            name_tokens = re.findall(r'\b[A-Za-z0-9_]+\b', name_val)
                            
                            for token in name_tokens:
                                # A token is considered a prohibited technical code if:
                                # - It is explicitly in our list of prohibited codes (FSP, TFT, DSD, CL)
                                # - It starts with CL_ or DSD_ (case-insensitive)
                                # - It contains an underscore, is in ALL CAPS (or starts with a letter and has numbers/underscores), and length >= 3
                                is_prohibited = (
                                    token in prohibited_codes or
                                    token.upper().startswith("CL_") or
                                    token.upper().startswith("DSD_") or
                                    (token.isupper() and '_' in token and len(token) >= 3)
                                )
                                
                                if is_prohibited:
                                    errors.append(
                                        f"{filename}, line {line_idx}: Node '{current_node_dcid}' name contains technical code '{token}' in: '{name_val}'"
                                    )
                                    failed = True
                                    break  # Only report one code error per name property to avoid log clutter

        self.write_log("\n--- Validation Results ---")
        if errors:
            self.write_log(f"Found {len(errors)} name constraint violations:")
            for err in errors[:50]:
                self.write_log(f"  - {err}")
            if len(errors) > 50:
                self.write_log(f"  ... and {len(errors) - 50} more errors.")
        else:
            self.write_log("No name constraint violations found (Rule 17 passed).")
            
        status = "FAILED" if failed else "PASSED"
        self.write_log(f"\nOverall Status: {status}")
        print(f"Rule 17 Validation complete. Results written to {self.log_file}")
        
        return not failed

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_17.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule17Validator(sys.argv[1], sys.argv[2])
    validator.validate()
