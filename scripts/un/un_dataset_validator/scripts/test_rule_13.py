"""
VALIDATION RULE:
================
# Rule 13.1: Statvar Name Template

## Requirement
The name assigned to a Statistical Variable (StatVar) must adhere to a specific template format to ensure consistency and readability across the Data Commons Project (DCP).

## Context & Rules
- According to the checklist, the required template for a StatVar name is:
  `"<series name> [<concept name>=<code name>, ...]"`
- This template provides a clear, human-readable summary of the underlying data series and the specific constraint properties (concepts and codes) that define the statistical variable.
- For example, if the series is "Unemployment Rate" and the concepts are "Age" and "Gender" with codes "15-24" and "Female" respectively, the name should be constructed as:
  `"Unemployment Rate [Age=15-24, Gender=Female]"`


"""
import os
import sys
import glob
import re

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))
from base_validator import BaseRuleValidator

class Rule13Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 13 (StatVar Name Template)")
        
        mcf_pattern = os.path.join(self.dataset_dir, "schema", f"*_stat_vars.mcf")
        mcf_files = glob.glob(mcf_pattern)

        if not mcf_files:
            self.write_log(f"No _stat_vars.mcf files found in {os.path.join(self.dataset_dir, 'schema')}")
            print(f"No _stat_vars.mcf files found.")
            return False

        total_files = len(mcf_files)
        failed_files = 0

        self.write_log(f"Output Schema Directory: {os.path.join(self.dataset_dir, 'schema')}\n")

        for mcf_path in sorted(mcf_files):
            filename = os.path.basename(mcf_path)
            errors = []
            
            with open(mcf_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            nodes = content.split('Node: dcid:')
            for node in nodes:
                if not node.strip():
                    continue
                if 'typeOf: dcid:StatisticalVariable' not in node and 'typeOf: dcs:StatisticalVariable' not in node:
                    continue
                    
                name_match = re.search(r'name:\s*"([^"]+)"', node)
                if not name_match:
                    # Depending on pipeline, some generic statvars might not have generated names, but we should flag it
                    # But wait, some might just be properties. We already filtered by typeOf: StatisticalVariable
                    errors.append(f"StatVar in {filename} is missing a 'name' property.")
                    continue
                    
                name_val = name_match.group(1)
                
                # Check template format: Base Name [Concept=Code, Concept=Code]
                # If there are no constraints, it might just be "Base Name"
                match = re.match(r'^(.+?)(?:\s+\[(.+)\])?$', name_val)
                if not match:
                    errors.append(f"StatVar name '{name_val}' in {filename} does not match expected overall format.")
                    continue
                
                constraints_str = match.group(2)
                if constraints_str:
                    # Look for Concept=Code patterns, handling commas in Code
                    # Assumes Concept does not contain '=' or ','
                    # and that concepts are separated by ', ' followed by a new Concept=
                    constraint_matches = re.finditer(r'([^,=]+)=(.+?)(?=(?:, [^,=]+=)|$)', constraints_str)
                    
                    found_constraints = False
                    for c_match in constraint_matches:
                        found_constraints = True
                        concept = c_match.group(1).strip()
                        code = c_match.group(2).strip()
                        if not concept or not code:
                            errors.append(f"Constraint in '{name_val}' has empty concept or code.")
                    
                    if not found_constraints:
                        errors.append(f"StatVar name '{name_val}' has brackets but no 'Concept=Code' format inside.")
                            
            if errors:
                failed_files += 1
                self.write_log(f"[{filename}] FAILED")
                for err in errors:
                    self.write_log(f"  - {err}")
                self.write_log("")
            else:
                self.write_log(f"[{filename}] PASSED")

        self.write_log(f"\nSummary:")
        self.write_log(f"Total MCFs Checked: {total_files}")
        self.write_log(f"Passed: {total_files - failed_files}")
        self.write_log(f"Failed: {failed_files}")

        print(f"Rule 13 Validation completed. {failed_files}/{total_files} files failed.")
        print(f"Details saved to {self.log_file}")
        
        return failed_files == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_13.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule13Validator(sys.argv[1], sys.argv[2])
    validator.validate()
