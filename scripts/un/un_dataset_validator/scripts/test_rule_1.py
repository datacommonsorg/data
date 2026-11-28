"""
VALIDATION RULE:
================
# Rule 1: 1:1 Mapping Validation (PV Maps)

## Requirement
Ensure all UN concepts and codes have a strict 1:1 mapping with the agency-specific DCP schema.

## Context & Rules (From Meeting Notes)
- There must be no duplicate properties assigned to a single concept.
- Within the Property-Value (PV) maps, the `event code` column must align perfectly with the `constraint property`.
- For example, if the concept is "age" or "poverty status", the `event code` must be "age" or "poverty status" exactly, maintaining consistency across the file.
- This rule applies strictly to the agency-specific schema rather than the base Data Commons mapping.


"""
import os
import sys
import glob
import csv

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator
from validator_utils import to_canonical_format

class Rule1Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 1 (1:1 Schema Mapping)")
        
        pattern = os.path.join(self.pvmap_dir, "CL_*_pvmap.csv")
        pvmap_files = glob.glob(pattern)
        
        if not pvmap_files:
            self.write_log(f"No CL_*_pvmap.csv files found in {self.pvmap_dir}")
            print(f"No CL_*_pvmap.csv files found in {self.pvmap_dir}. Log written to {self.log_file}")
            return False
            
        total_files = len(pvmap_files)
        failed_files = 0
        
        concept_to_prop = {}
        prop_to_concept = {}
        
        global_errors = []
        file_specific_errors = {}
        
        for filepath in pvmap_files:
            filename = os.path.basename(filepath)
            file_errors = []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if 'UnConcept' not in reader.fieldnames or 'ConstraintProp' not in reader.fieldnames:
                    file_errors.append("Missing required columns: 'UnConcept' or 'ConstraintProp'")
                    file_specific_errors[filename] = file_errors
                    failed_files += 1
                    continue
                
                for row_num, row in enumerate(reader, start=2):
                    un_concept = row.get('UnConcept', '').strip()
                    constraint_prop = row.get('ConstraintProp', '').strip()
                    
                    if not un_concept or not constraint_prop:
                        continue
                        
                    canon_concept = to_canonical_format(un_concept)
                    canon_prop = to_canonical_format(constraint_prop)
                    
                    if canon_concept in ['series', 'geography', 'timeperiod', 'obsvalue']:
                        continue
                        
                    if canon_concept != canon_prop:
                        file_errors.append(f"File {filename}, Row {row_num}: Alignment mismatch. Canonical UnConcept '{canon_concept}' != Canonical ConstraintProp '{canon_prop}'. Original: '{un_concept}' vs '{constraint_prop}'")
                        
                    if un_concept in concept_to_prop:
                        if concept_to_prop[un_concept] != constraint_prop:
                            global_errors.append(f"Duplicate assignment for UnConcept '{un_concept}': mapped to both '{concept_to_prop[un_concept]}' and '{constraint_prop}' (found in {filename})")
                    else:
                        concept_to_prop[un_concept] = constraint_prop
                        
                    if constraint_prop in prop_to_concept:
                        if prop_to_concept[constraint_prop] != un_concept:
                             global_errors.append(f"Duplicate assignment for ConstraintProp '{constraint_prop}': mapped to both '{prop_to_concept[constraint_prop]}' and '{un_concept}' (found in {filename})")
                    else:
                        prop_to_concept[constraint_prop] = un_concept
                        
            if file_errors:
                file_specific_errors[filename] = file_errors
                failed_files += 1

        self.write_log(f"--- Global 1:1 Mapping Violations ---")
        if not global_errors:
            self.write_log("No global 1:1 mapping violations detected.")
        else:
            for err in global_errors:
                self.write_log(f"- {err}")
                
        self.write_log(f"\n--- File-Specific Alignment Violations ---")
        if not file_specific_errors:
            self.write_log("No alignment violations detected.")
        else:
            for filename, errors in file_specific_errors.items():
                self.write_log(f"\nFAILED FILE: {filename}")
                for err in errors[:20]:
                    self.write_log(f"  - {err}")
                if len(errors) > 20:
                     self.write_log(f"  ... and {len(errors) - 20} more errors.")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total files processed: {total_files}")
        self.write_log(f"Files with alignment errors: {len(file_specific_errors)}")
        self.write_log(f"Total global 1:1 violations: {len(global_errors)}")
        
        status = "PASSED" if not global_errors and not file_specific_errors else "FAILED"
        self.write_log(f"Overall Status: {status}")
        print(f"Rule 1 Validation complete. Results written to {self.log_file}")
        
        return status == "PASSED"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_1.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule1Validator(sys.argv[1], sys.argv[2])
    validator.validate()