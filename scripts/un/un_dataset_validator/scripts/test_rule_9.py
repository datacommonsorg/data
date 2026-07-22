"""
VALIDATION RULE:
================
# Rule 9: Frequency to observationPeriod

## Objective
Ensure that the `FREQUENCY` column in the source data correctly maps to the Data Commons `observationPeriod` property in the output CSV, adhering to the mapping defined in the common Property-Value (PV) map.

## File References
- **Input Data File:** Data file containing the `FREQUENCY` column.
- **Common PV Map:** `all_data/pvmap/CL_FREQUENCY_pvmap_obsperiod.csv`
- **Output CSV:** Transcoded data file (e.g., `processed_data/*_data.csv`).


"""
import os
import sys
import glob
import csv

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator
from validator_utils import get_input_file_path

def load_freq_map(pv_map_path):
    freq_map = {}
    if not os.path.exists(pv_map_path):
        return freq_map
    with open(pv_map_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            un_code = row.get('UnCode', '').strip().strip('"')
            obs_period = row.get('ConstraintPropValue', '').strip()
            if un_code and obs_period:
                freq_map[un_code] = obs_period
    return freq_map

class Rule9Validator(BaseRuleValidator):
    def validate_file(self, output_csv_path, freq_map):
        filename = os.path.basename(output_csv_path)
        
        output_mapping = {}
        target_col = 'observationPeriod'
        typo_found = False
        
        with open(output_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'observationPeriod' not in reader.fieldnames:
                if 'opservationPeriod' in reader.fieldnames:
                    typo_found = True
                    target_col = 'opservationPeriod'
                else:
                    # Missing both
                    return {"status": "FAILED", "errors": ["Target column 'observationPeriod' not found in output CSV."]}

            for row in reader:
                if '#input' in row:
                    parts = row['#input'].split(':')
                    if len(parts) >= 2:
                        input_filename = parts[0]
                        try:
                            line_num = int(parts[1])
                            output_mapping[(input_filename, line_num)] = row.get(target_col, '').strip()
                        except ValueError:
                            pass
        
        if not output_mapping:
            return {"status": "SKIPPED", "reason": "No #input mapping found in output CSV"}
            
        input_filename = list(output_mapping.keys())[0][0]
        input_csv_path = get_input_file_path(self.dataset_name, input_filename, self.input_data_dir)
        
        if not input_csv_path or not os.path.exists(input_csv_path):
            return {"status": "FAILED", "errors": [f"Input file not found: {input_filename}"]}

        errors = []
        if typo_found:
            errors.append("Typo found in output CSV header: 'opservationPeriod' instead of 'observationPeriod'.")
            
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # FREQUENCY might not be present in all files, but if it is, validate it
            if 'FREQUENCY' not in reader.fieldnames and 'FREQ' not in reader.fieldnames:
                 return {"status": "SKIPPED", "reason": "No FREQUENCY column in input CSV"}

            freq_col = 'FREQUENCY' if 'FREQUENCY' in reader.fieldnames else 'FREQ'
                 
            for line_idx, row in enumerate(reader, start=2):
                input_freq = row.get(freq_col, '').strip()
                if not input_freq:
                    continue
                    
                expected_obs_period = freq_map.get(input_freq)
                if not expected_obs_period:
                    continue
                
                mapping_key = (input_filename, line_idx)
                if mapping_key in output_mapping:
                    actual_obs_period = output_mapping[mapping_key]
                    if actual_obs_period != expected_obs_period:
                        errors.append(f"File {input_filename}, Line {line_idx}: expected observationPeriod '{expected_obs_period}' for frequency '{input_freq}', but got '{actual_obs_period}'")

        if errors:
            return {"status": "FAILED", "errors": errors}
            
        return {"status": "PASSED"}

    def validate(self):
        self.setup_logging("Rule 9 (Frequency to observationPeriod Mapping)")
        
        # global pvmap directory
        # Use the parent directory of the provided dataset directory to find the global pvmap
        # E.g. if dataset_dir is /path/to/data/dataset_name, global pvmap should be /path/to/data/pvmap
        global_pvmap_dir = os.path.join(os.path.dirname(self.dataset_dir), "pvmap")
        
        # Check local dataset pvmap dir first, then global
        pv_map_path = os.path.join(self.pvmap_dir, "CL_FREQUENCY_pvmap_obsperiod.csv")
        if not os.path.exists(pv_map_path):
             pv_map_path = os.path.join(self.pvmap_dir, "common_pvmap_obs.csv")
             if not os.path.exists(pv_map_path):
                 pv_map_path = os.path.join(global_pvmap_dir, "CL_FREQUENCY_pvmap_obsperiod.csv")
                 if not os.path.exists(pv_map_path):
                     pv_map_path = os.path.join(global_pvmap_dir, "common_pvmap_obs.csv")
             
        self.write_log(f"Loading Frequency PV Map from {pv_map_path}...")
        freq_map = load_freq_map(pv_map_path)
        self.write_log(f"Loaded {len(freq_map)} frequency mappings.")
        
        if not freq_map:
             self.write_log(f"Failed to load frequency mapping from {pv_map_path}")
             print(f"Failed to load frequency mapping from {pv_map_path}. Log written to {self.log_file}")
             return False
             
        pattern = os.path.join(self.processed_dir, "*_data.csv")
        output_files = glob.glob(pattern)
        
        if not output_files:
            self.write_log(f"No *_data.csv files found in {self.processed_dir}")
            print(f"No *_data.csv files found in {self.processed_dir}. Log written to {self.log_file}")
            return False
            
        total = len(output_files)
        passed = 0
        failed = 0
        skipped = 0
        failed_details = []
        
        for filepath in output_files:
            result = self.validate_file(filepath, freq_map)
            
            if result["status"] == "PASSED":
                passed += 1
            elif result["status"] == "SKIPPED":
                skipped += 1
            else:
                failed += 1
                failed_details.append({"filename": os.path.basename(filepath), "errors": result["errors"]})

        self.write_log(f"--- Detailed Failure Report ---")
        if failed == 0:
            self.write_log("No validation failures detected.")
        else:
            for failure in failed_details:
                self.write_log(f"\nFAILED FILE: {failure['filename']}")
                errors = failure['errors']
                self.write_log(f"Total errors in this file: {len(errors)}")
                
                limit = min(10, len(errors))
                for err in errors[:limit]:
                    self.write_log(f"  - {err}")
                if len(errors) > limit:
                    self.write_log(f"  ... and {len(errors) - limit} more errors.")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total files processed: {total}")
        self.write_log(f"Passed: {passed}")
        self.write_log(f"Failed: {failed}")
        self.write_log(f"Skipped: {skipped}")

        status_passed = failed == 0
        self.write_log(f"Overall Status: {'PASSED' if status_passed else 'FAILED'}")
        print(f"Rule 9 Validation complete. Results written to {self.log_file}")
        return status_passed

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_9.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule9Validator(sys.argv[1], sys.argv[2])
    validator.validate()
