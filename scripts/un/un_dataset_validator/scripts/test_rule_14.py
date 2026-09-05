"""
VALIDATION RULE:
================
# Rule 14: Duplicate Checks
Ensures there are no duplicated rows across the dataset observation files.
"""
import os
import glob
import pandas as pd
from base_validator import BaseRuleValidator

class Rule14Validator(BaseRuleValidator):
    """
    Rule 14 Validator: Checks for duplicate observations in the generated CSV files.
    
    A duplicate observation is defined as multiple rows having the same combination of:
    - variableMeasured (StatVar)
    - observationAbout (Place)
    - observationDate (Date)
    """

    def validate(self):
        self.setup_logging("Rule 14 (Observation Uniqueness)")
        
        pattern = os.path.join(self.processed_dir, "*_data.csv")
        csv_files = glob.glob(pattern)
        
        if not csv_files:
            self.write_log(f"No *_data.csv files found in {self.processed_dir}")
            print(f"No *_data.csv files found in {self.processed_dir}. Log written to {self.log_file}")
            return False

        total_files = len(csv_files)
        failed_files = 0
        total_duplicates = 0
        
        # Columns that make up the unique composite key in Data Commons
        key_cols = ['variableMeasured', 'observationAbout', 'observationDate']

        for filepath in csv_files:
            filename = os.path.basename(filepath)
            
            try:
                # Read CSV, forcing all to string to prevent type issues
                df = pd.read_csv(filepath, dtype=str)
                
                # Check if the required columns exist
                missing_cols = [col for col in key_cols if col not in df.columns]
                if missing_cols:
                    self.write_log(f"File {filename}: Missing required columns for uniqueness check: {missing_cols}")
                    failed_files += 1
                    continue
                
                # Find duplicates
                dups = df[df.duplicated(subset=key_cols, keep=False)]
                
                if not dups.empty:
                    failed_files += 1
                    dup_count = len(dups)
                    total_duplicates += dup_count
                    
                    self.write_log(f"\nFAILED FILE: {filename}")
                    self.write_log(f"Found {dup_count} duplicate rows.")
                    
                    # Sort so duplicates are grouped together in the log
                    dups_sorted = dups.sort_values(by=key_cols)
                    
                    # Log up to the first 20 duplicate lines for context
                    # The index + 2 assumes a 1-based header (index 0 is data row 1 -> line 2)
                    count = 0
                    for idx, row in dups_sorted.iterrows():
                        if count >= 20:
                            self.write_log(f"  ... and {dup_count - 20} more duplicate rows.")
                            break
                            
                        line_num = idx + 2 
                        stat_var = row['variableMeasured']
                        place = row['observationAbout']
                        date = row['observationDate']
                        val = row.get('value', 'N/A')
                        
                        self.write_log(f"  - File {filename}, Line {line_num}: Duplicate observation -> StatVar: '{stat_var}', Place: '{place}', Date: '{date}', Value: '{val}'")
                        count += 1
                        
            except Exception as e:
                self.write_log(f"File {filename}: Error processing file: {e}")
                failed_files += 1

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total output files processed: {total_files}")
        self.write_log(f"Files with duplicates: {failed_files}")
        self.write_log(f"Total duplicate rows detected: {total_duplicates}")
        
        status = "PASSED" if failed_files == 0 else "FAILED"
        self.write_log(f"Overall Status: {status}")

        print(f"Rule 14 Validation completed. {failed_files}/{total_files} files failed with duplicates.")
        print(f"Details saved to {self.log_file}")
        
        return failed_files == 0

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="Run Rule 14 Validation (Observation Uniqueness)")
    parser.add_argument("--dataset", required=True, help="Dataset name (e.g., sdg_q1-2026)")
    parser.add_argument("--dataset_dir", required=True, help="Path to the dataset directory")
    args = parser.parse_args()
    
    validator = Rule14Validator(args.dataset, args.dataset_dir)
    validator.validate()