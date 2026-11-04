"""
VALIDATION RULE:
================
# Rule 11: StatVar DCID Format & Special Characters

## Overview
This rule validates the structural format of the Data Commons Identifier (DCID) generated for each Statistical Variable (StatVar). The DCID must strictly adhere to a specific templated format, and any illegal or special characters within the originating codes must be converted to underscores (`_`) to ensure valid identifier syntax.

## Files Involved
- **Output:** `output_stat_vars.mcf` (Specifically examining the `Node: dcid:...` lines).


"""
import os
import sys
import glob
import re

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))
from base_validator import BaseRuleValidator

class Rule11Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 11 (StatVar DCID Format)")
        
        pattern = os.path.join(self.processed_dir, "*_stat_vars.mcf")
        mcf_files = glob.glob(pattern)
        
        if not mcf_files:
            self.write_log(f"No *_stat_vars.mcf files found in {self.processed_dir}")
            print(f"No *_stat_vars.mcf files found in {self.processed_dir}. Log written to {self.log_file}")
            return False
            
        total = len(mcf_files)
        passed = 0
        failed = 0
        failed_details = []
        
        # Regex to match the expected format:
        # dcid:undata/<agency>/<SERIES>[.<CONCEPT>--<CODE>__...]
        # We allow a-zA-Z, 0-9, and underscores. 
        dcid_regex = re.compile(r"^dcid:[a-zA-Z0-9_]+/[a-zA-Z0-9_]+/[A-Z0-9_]+(\.[A-Z0-9_]+--[a-zA-Z0-9_]+(__[A-Z0-9_]+--[a-zA-Z0-9_]+)*)?$")
        
        for filepath in mcf_files:
            filename = os.path.basename(filepath)
            errors = []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_idx, line in enumerate(f, start=1):
                    line = line.strip()
                    if line.startswith("Node: dcid:"):
                        dcid = line[6:] # Strip 'Node: '
                        
                        if not dcid_regex.match(dcid):
                            errors.append(f"File {filename}, Line {line_idx}: Invalid DCID format: '{dcid}'")
            
            if errors:
                failed += 1
                failed_details.append({"filename": filename, "errors": errors})
            else:
                passed += 1
                
        self.write_log(f"--- Detailed Failure Report ---")
        if failed == 0:
            self.write_log("No validation failures detected.")
        else:
            for failure in failed_details:
                self.write_log(f"\nFAILED FILE: {failure['filename']}")
                errors = failure['errors']
                self.write_log(f"Total format errors in this file: {len(errors)}")
                
                limit = min(10, len(errors))
                for err in errors[:limit]:
                    self.write_log(f"  - {err}")
                if len(errors) > limit:
                    self.write_log(f"  ... and {len(errors) - limit} more errors.")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total MCF files processed: {total}")
        self.write_log(f"Passed: {passed}")
        self.write_log(f"Failed: {failed}")

        status_passed = failed == 0
        self.write_log(f"Overall Status: {'PASSED' if status_passed else 'FAILED'}")
        print(f"Rule 11 Validation complete. Results written to {self.log_file}")
        return status_passed

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_11.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule11Validator(sys.argv[1], sys.argv[2])
    validator.validate()