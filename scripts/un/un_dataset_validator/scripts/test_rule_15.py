"""
VALIDATION RULE:
================
# Rule 15: Duplicate Properties in Statistical Variables

## Requirement
Ensure there are no repeated property or concept codes assigned within a single Statistical Variable definition in the generated MCF files.

## Context & Rules
- Read `*_stat_vars.mcf` files in the output directory.
- For each `Node: dcid:...` block, track all the properties defined.
- If any property key (e.g., `age:`, `measurementMethod:`) appears more than once for a single node, flag it as an error.
"""

import os
import glob
import sys

# Ensure the scripts directory is in sys.path
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator

class Rule15Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 15 (Duplicate StatVar Properties)")
        
        # Look for MCF files in the processed directory
        pattern = os.path.join(self.processed_dir, "*_stat_vars.mcf")
        mcf_files = glob.glob(pattern)
        
        # Also check the dataset root if they are stored there
        if not mcf_files:
            pattern = os.path.join(self.dataset_dir, "*_stat_vars.mcf")
            mcf_files = glob.glob(pattern)
            
        if not mcf_files:
            # Fallback to dc_generated if present
            pattern = os.path.join(self.dc_generated_dir, "*_stat_vars.mcf")
            mcf_files = glob.glob(pattern)

        if not mcf_files:
            self.write_log(f"No *_stat_vars.mcf files found in {self.processed_dir}, {self.dataset_dir}, or {self.dc_generated_dir}")
            print(f"No *_stat_vars.mcf files found. Log written to {self.log_file}")
            return False

        total_files = len(mcf_files)
        failed_files = 0
        total_violations = 0
        
        for filepath in mcf_files:
            filename = os.path.basename(filepath)
            file_errors = []
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    current_node = None
                    seen_properties = set()
                    
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                            
                        if line.startswith('Node:'):
                            current_node = line.split('Node:')[1].strip()
                            seen_properties = set()
                            continue
                            
                        if current_node and ':' in line:
                            # Split on the first colon to get the property key
                            parts = line.split(':', 1)
                            prop_key = parts[0].strip()
                            
                            # Only track properties, not comments or multiline continuations without colons
                            if prop_key in seen_properties:
                                error_msg = f"File {filename}, Line {line_num}: Duplicate property '{prop_key}' found in Node '{current_node}'"
                                file_errors.append(error_msg)
                                total_violations += 1
                            else:
                                seen_properties.add(prop_key)
                                
            except Exception as e:
                file_errors.append(f"File {filename}: Error processing file: {e}")

            if file_errors:
                failed_files += 1
                self.write_log(f"\nFAILED FILE: {filename}")
                # Log up to 20 errors per file
                for err in file_errors[:20]:
                    self.write_log(f"  - {err}")
                if len(file_errors) > 20:
                    self.write_log(f"  ... and {len(file_errors) - 20} more errors.")
                    
        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total output files processed: {total_files}")
        self.write_log(f"Files with duplicate properties: {failed_files}")
        self.write_log(f"Total duplicate properties detected: {total_violations}")
        
        status = "PASSED" if failed_files == 0 else "FAILED"
        self.write_log(f"Overall Status: {status}")

        print(f"Rule 15 Validation completed. {failed_files}/{total_files} files failed.")
        print(f"Details saved to {self.log_file}")
        
        return failed_files == 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Rule 15 Validation (Duplicate StatVar Properties)")
    parser.add_argument("--dataset", required=True, help="Dataset name (e.g., sdg_q1-2026)")
    parser.add_argument("--dataset_dir", required=True, help="Path to the dataset directory")
    args = parser.parse_args()
    
    validator = Rule15Validator(args.dataset, args.dataset_dir)
    validator.validate()
