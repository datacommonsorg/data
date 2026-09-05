"""
VALIDATION RULE:
================
# Rule 4: Time Period to observationDate

## Objective
Ensure that the `TIME_PERIOD` (or `timePeriod`) column in the source data accurately maps to the Data Commons `observationDate` property in the output CSV, adhering to the new conversion requirements for complex formats.

## File References
- **Input Data File:** Source data file containing the `TIME_PERIOD` column.
- **Output CSV:** Transcoded data file (e.g., `processed_data/*_data.csv`).


"""
import os
import sys
import glob
import random
import csv

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator
from validator_utils import get_input_file_path

class Rule4Validator(BaseRuleValidator):
    def validate_file(self, output_csv_path):
        output_mapping = {}
        with open(output_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'observationDate' not in reader.fieldnames:
                return {"status": "FAILED", "errors": ["Output CSV missing 'observationDate' column."]}
            if '#input' not in reader.fieldnames:
                return {"status": "SKIPPED", "reason": "No #input mapping found in output CSV"}
                
            for row in reader:
                parts = row['#input'].split(':')
                if len(parts) >= 2:
                    input_filename = parts[0]
                    try:
                        line_num = int(parts[1])
                        output_mapping[(input_filename, line_num)] = row.get('observationDate', '').strip()
                    except ValueError:
                        pass

        if not output_mapping:
            return {"status": "SKIPPED", "reason": "No valid #input mapping parsed"}

        input_filename = list(output_mapping.keys())[0][0]
        input_csv_path = get_input_file_path(self.dataset_name, input_filename, self.input_data_dir)
        
        if not input_csv_path or not os.path.exists(input_csv_path):
            return {"status": "FAILED", "errors": [f"Input file not found: {input_filename}"]}

        errors = []
        
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            time_col = None
            for col in reader.fieldnames:
                if col and col.upper() == 'TIME_PERIOD':
                    time_col = col
                    break
                    
            if not time_col:
                return {"status": "FAILED", "errors": [f"Input CSV missing 'TIME_PERIOD' column (case-insensitive). Found: {reader.fieldnames}"]}

            for line_idx, row in enumerate(reader, start=2):
                mapping_key = (input_filename, line_idx)
                if mapping_key in output_mapping:
                    actual_obs_date = output_mapping[mapping_key]
                    input_time = str(row.get(time_col, '')).strip()
                    
                    yyyy_format = input_time[:4] if len(input_time) >= 4 else input_time
                    
                    if actual_obs_date == yyyy_format:
                        continue
                        
                    if actual_obs_date == input_time:
                        continue
                        
                    if '/' in input_time:
                        start_date = input_time.split('/')[0]
                        if actual_obs_date == start_date:
                            continue
                        errors.append(f"File {input_filename}, Line {line_idx}: expected '{yyyy_format}', '{start_date}', or '{input_time}', but got '{actual_obs_date}'")
                    else:
                        errors.append(f"File {input_filename}, Line {line_idx}: expected '{yyyy_format}' or '{input_time}', but got '{actual_obs_date}'")

        if errors:
            return {"status": "FAILED", "errors": errors}
            
        return {"status": "PASSED"}

    def validate(self):
        self.setup_logging("Rule 4 (Time Period Mapping)")
        
        pattern = os.path.join(self.processed_dir, "*_data.csv")
        output_files = glob.glob(pattern)
        
        if not output_files:
            self.write_log(f"No *_data.csv files found in {self.processed_dir}")
            print(f"No *_data.csv files found in {self.processed_dir}")
            return False
            
        total = len(output_files)
        passed = 0
        failed = 0
        skipped = 0
        failed_details = []
        
        for filepath in output_files:
            result = self.validate_file(filepath)
            
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
                self.write_log(f"Total row mismatch errors in this file: {len(errors)}")
                
                sampled_errors = random.sample(errors, min(10, len(errors)))
                self.write_log(f"Sampled mismatch errors (up to 10):")
                for err in sampled_errors:
                    self.write_log(f"  - {err}")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total files processed: {total}")
        self.write_log(f"Passed: {passed}")
        self.write_log(f"Failed: {failed}")
        self.write_log(f"Skipped: {skipped}")

        print(f"Rule 4 Validation complete. Results written to {self.log_file}")
        return failed == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_4.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule4Validator(sys.argv[1], sys.argv[2])
    validator.validate()