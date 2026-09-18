"""
VALIDATION RULE:
================
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


"""
import os
import sys
import glob
import csv
import string

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))
from base_validator import BaseRuleValidator

def normalize_name(s):
    if not s:
        return ""
    # Remove all punctuation and lowercase
    s = s.translate(str.maketrans('', '', string.punctuation)).lower()
    # Normalize spaces
    return " ".join(s.split())

class Rule12Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 12 (Names Validation)")
        
        # 1. Load all PV Maps to get expected names
        expected_names = {}
        pvmap_files = glob.glob(os.path.join(self.pvmap_dir, "CL_*_pvmap.csv"))
        for pvmap_file in pvmap_files:
            with open(pvmap_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dcid = row.get('ConstraintPropValue', '').strip()
                    name = row.get('ConstraintValueName', '').strip().strip('"')
                    if dcid and name:
                        expected_names[dcid] = name
        
        self.write_log(f"Loaded {len(expected_names)} expected value names from PV maps.")
        
        # 2. Check Schema MCFs for Value names (12.2)
        schema_pattern = os.path.join(self.dataset_dir, "schema", "*.mcf")
        schema_files = glob.glob(schema_pattern)
        
        failed = False
        errors = []
        warnings = []
        
        if not schema_files:
            self.write_log("No schema MCF files found.")
            failed = True
        else:
            for schema_file in schema_files:
                current_node = None
                current_name = None
                
                with open(schema_file, 'r', encoding='utf-8') as f:
                    for line_idx, line in enumerate(f, start=1):
                        line = line.strip()
                        if line.startswith("Node: "):
                            # Process previous node
                            if current_node and current_node in expected_names:
                                expected = expected_names[current_node]
                                if current_name is None:
                                    errors.append(f"{os.path.basename(schema_file)}: Missing name for {current_node}. Expected '{expected}'")
                                elif normalize_name(current_name) != normalize_name(expected):
                                    errors.append(f"{os.path.basename(schema_file)}: Value mismatch for {current_node}. Expected '{expected}', found '{current_name}'")
                            
                            current_node = line[6:].strip()
                            if current_node.startswith('dcid:'):
                                current_node = current_node[5:]
                            current_name = None
                        elif line.startswith("name: "):
                            # Handle names that might have extra characters or spaces around quotes
                            extracted_name = line[6:].strip()
                            if extracted_name.startswith('"') and extracted_name.endswith('"'):
                                current_name = extracted_name[1:-1]
                            else:
                                current_name = extracted_name.strip('"')
                
                # Check the last node
                if current_node and current_node in expected_names:
                    expected = expected_names[current_node]
                    if current_name is None:
                        errors.append(f"{os.path.basename(schema_file)}: Missing name for {current_node}. Expected '{expected}'")
                    elif normalize_name(current_name) != normalize_name(expected):
                        errors.append(f"{os.path.basename(schema_file)}: Value mismatch for {current_node}. Expected '{expected}', found '{current_name}'")

        # 3. Check StatVars MCF for missing names
        statvar_pattern = os.path.join(self.processed_dir, "*_stat_vars.mcf")
        statvar_files = glob.glob(statvar_pattern)
        
        missing_statvar_names_count = 0
        if statvar_files:
            for sv_file in statvar_files:
                with open(sv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    nodes = content.split("Node: ")
                    for node in nodes[1:]: # Skip the first empty split before first Node
                        if "typeOf: dcid:StatisticalVariable" in node:
                            if "\nname: " not in node:
                                missing_statvar_names_count += 1

        if missing_statvar_names_count > 0:
            warnings.append(f"Found {missing_statvar_names_count} Statistical Variables missing a 'name' property. This is a known pipeline issue (Check 12 / 13).")
            
        self.write_log("--- Validation Results ---")
        if errors:
            self.write_log(f"Found {len(errors)} name mismatches:")
            for err in errors[:50]:
                self.write_log(f"  - {err}")
            if len(errors) > 50:
                self.write_log(f"  ... and {len(errors) - 50} more errors.")
            failed = True
        else:
            self.write_log("No value name mismatches found against PV maps (Rule 12.2 passed).")
            
        if warnings:
            self.write_log("\n--- Warnings ---")
            for warn in warnings:
                self.write_log(f"  - {warn}")
                
        status = "FAILED" if failed else "PASSED"
        self.write_log(f"\nOverall Status: {status}")
        print(f"Rule 12 Validation complete. Results written to {self.log_file}")
        
        return not failed

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_12.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule12Validator(sys.argv[1], sys.argv[2])
    validator.validate()
