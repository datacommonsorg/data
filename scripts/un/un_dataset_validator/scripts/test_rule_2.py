"""
VALIDATION RULE:
================
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


"""
import os
import sys
import glob
import random

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator

def parse_mcf(filepath):
    nodes = []
    current_node = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_node:
                    nodes.append(current_node)
                    current_node = {}
                continue
            if line.startswith('Node:'):
                if current_node:
                    nodes.append(current_node)
                current_node = {'Node': line.split(':', 1)[1].strip()}
            elif ':' in line:
                key, val = line.split(':', 1)
                current_node[key.strip()] = val.strip()
    if current_node:
        nodes.append(current_node)
    return nodes

class Rule2Validator(BaseRuleValidator):
    def validate_file(self, mcf_filepath: str, expected_series_code: str, agency_name: str) -> dict:
        agency_upper = agency_name.upper()
        expected_population_type = f"dcid:UN_{agency_upper}_SERIES-{expected_series_code}"
        filename = os.path.basename(mcf_filepath)
        
        mcf_nodes = parse_mcf(mcf_filepath) 
        errors = []
        
        for node in mcf_nodes:
            if node.get('typeOf') == 'dcid:StatisticalVariable':
                node_id = node.get('Node')
                actual_population_type = node.get('populationType')
                
                if not actual_population_type:
                    errors.append(f"File {filename}: Node {node_id} is missing 'populationType'.")
                elif actual_population_type != expected_population_type:
                    errors.append(f"File {filename}: Node {node_id} has incorrect populationType. Expected '{expected_population_type}', got '{actual_population_type}'.")
                    
        if errors:
            return {"status": "FAILED", "errors": errors}
        return {"status": "PASSED"}

    def validate(self):
        self.setup_logging("Rule 2 (Series to Population Type)")
        
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
        
        for filepath in mcf_files:
            filename = os.path.basename(filepath)
            
            if "_OBS_" not in filename:
                continue
                
            parts = filename.split("_OBS_")
            prefix = parts[0]
            agency = prefix.split("_")[0]
            
            suffix = parts[1]
            if not suffix.endswith("_data_stat_vars.mcf"):
                continue
                
            series_code = suffix.replace("_data_stat_vars.mcf", "")
            
            result = self.validate_file(filepath, series_code, agency)
            
            if result["status"] == "PASSED":
                passed += 1
            else:
                failed += 1
                failed_details.append({"filename": filename, "errors": result["errors"]})

        self.write_log(f"--- Detailed Failure Report ---")
        if failed == 0:
            self.write_log("No failures detected.")
        else:
            for failure in failed_details:
                self.write_log(f"\nFAILED FILE: {failure['filename']}")
                errors = failure['errors']
                self.write_log(f"Total nodes failed in this file: {len(errors)}")
                
                # Sample up to 10 random errors
                sampled_errors = random.sample(errors, min(10, len(errors)))
                self.write_log(f"Sampled failed nodes (up to 10):")
                for err in sampled_errors:
                    self.write_log(f"  - {err}")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total files processed: {total}")
        self.write_log(f"Passed: {passed}")
        self.write_log(f"Failed: {failed}")

        print(f"Rule 2 Validation complete. Results written to {self.log_file}")
        return failed == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_2.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule2Validator(sys.argv[1], sys.argv[2])
    validator.validate()